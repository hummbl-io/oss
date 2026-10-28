package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
)

func integrityWorkspace(t *testing.T) (*WagsWorkspace, string) {
	t.Helper()
	root := t.TempDir()
	target := filepath.Join(root, "target.txt")
	if err := os.WriteFile(target, []byte("original target"), 0644); err != nil {
		t.Fatal(err)
	}
	ws, err := NewWagsWorkspace(filepath.Join(root, "workspace"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := ws.InitReview(target, "code", "", "reviewer", "original"); err != nil {
		t.Fatal(err)
	}
	return ws, target
}

func TestKeyedVerificationRejectsRemovedSignature(t *testing.T) {
	ws, _ := integrityWorkspace(t)
	if err := ws.RegisterReviewer("original", "reviewer", "test-key", "reviewer"); err != nil {
		t.Fatal(err)
	}
	entry, err := ws.SubmitEntry("original", "reviewer", "review", nil, "block", "test-key")
	if err != nil {
		t.Fatal(err)
	}
	entry.Verdict = "approve"
	if err := signEntry(entry, ""); err != nil {
		t.Fatal(err)
	}
	data, err := json.Marshal(entry)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(ws.ReviewsDir, "original", "reviewer.jsonl"), append(data, '\n'), 0644); err != nil {
		t.Fatal(err)
	}
	valid, errs, err := ws.VerifyReview("original", map[string]string{"reviewer": "test-key"})
	if err != nil || valid || !strings.Contains(strings.Join(errs, " "), "signature") {
		t.Fatalf("forged unsigned approval accepted: %v %v %v", valid, errs, err)
	}
}

func TestSignedStreamCannotReplayIntoAnotherReview(t *testing.T) {
	ws, target := integrityWorkspace(t)
	if _, err := ws.InitReview(target, "code", "", "reviewer", "other"); err != nil {
		t.Fatal(err)
	}
	for _, rid := range []string{"original", "other"} {
		if err := ws.RegisterReviewer(rid, "reviewer", "test-key", "reviewer"); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := ws.SubmitEntry("original", "reviewer", "review", nil, "approve", "test-key"); err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(filepath.Join(ws.ReviewsDir, "original", "reviewer.jsonl"))
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(ws.ReviewsDir, "other", "reviewer.jsonl"), data, 0644); err != nil {
		t.Fatal(err)
	}
	valid, errs, err := ws.VerifyReview("other", map[string]string{"reviewer": "test-key"})
	if err != nil || valid {
		t.Fatalf("foreign review accepted: %v %v %v", valid, errs, err)
	}
	result, err := ws.ConvergeReview("other")
	if err != nil || result["overall_verdict"] != "BLOCK" {
		t.Fatalf("foreign approval counted: %v %v", result, err)
	}
}

func TestInitReviewPreservesExistingApproval(t *testing.T) {
	ws, target := integrityWorkspace(t)
	if err := ws.RegisterReviewer("original", "reviewer", "test-key", "reviewer"); err != nil {
		t.Fatal(err)
	}
	if _, err := ws.SubmitEntry("original", "reviewer", "review", nil, "approve", "test-key"); err != nil {
		t.Fatal(err)
	}
	manifest := filepath.Join(ws.ReviewsDir, "original", "target.json")
	before, err := os.ReadFile(manifest)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(target, []byte("different, unreviewed target"), 0644); err != nil {
		t.Fatal(err)
	}
	if _, err := ws.InitReview(target, "code", "", "reviewer", "original"); !os.IsExist(err) {
		t.Fatalf("expected existing-review rejection, got %v", err)
	}
	after, err := os.ReadFile(manifest)
	if err != nil || string(before) != string(after) {
		t.Fatalf("existing manifest changed: %v", err)
	}
}

func TestConcurrentRegistrationKeepsEveryReviewer(t *testing.T) {
	ws, _ := integrityWorkspace(t)
	const count = 24
	start := make(chan struct{})
	errors := make(chan error, count)
	var wg sync.WaitGroup
	for i := 0; i < count; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			<-start
			errors <- ws.RegisterReviewer("original", fmt.Sprintf("reviewer-%d", i), "", "reviewer")
		}(i)
	}
	close(start)
	wg.Wait()
	close(errors)
	for err := range errors {
		if err != nil {
			t.Fatal(err)
		}
	}
	registry := registeredReviewers(filepath.Join(ws.ReviewsDir, "original"))
	if len(registry) != count {
		t.Fatalf("lost registrations: got %d, want %d", len(registry), count)
	}
}

func TestNumericMetadataSurvivesSignedWriteRead(t *testing.T) {
	ws, _ := integrityWorkspace(t)
	if err := ws.RegisterReviewer("original", "reviewer", "test-key", "reviewer"); err != nil {
		t.Fatal(err)
	}
	metadata := map[string]interface{}{"score": 1.0, "nested": []interface{}{2.0, map[string]interface{}{"value": 3.0}}}
	if _, err := ws.SubmitEntryWithMetadata("original", "reviewer", "review", nil, "approve", "test-key", metadata); err != nil {
		t.Fatal(err)
	}
	valid, errs, err := ws.VerifyReview("original", map[string]string{"reviewer": "test-key"})
	if err != nil || !valid {
		t.Fatalf("signed round-trip rejected: %v %v %v", valid, errs, err)
	}
}

func TestBadRegistryIsNotSilentlyReplaced(t *testing.T) {
	ws, _ := integrityWorkspace(t)
	path := filepath.Join(ws.ReviewsDir, "original", "reviewers.json")
	if err := os.WriteFile(path, []byte("broken JSON"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := ws.RegisterReviewer("original", "reviewer", "", "reviewer"); err == nil {
		t.Fatal("corrupt registry was accepted")
	}
	data, err := os.ReadFile(path)
	if err != nil || string(data) != "broken JSON" {
		t.Fatalf("registry replaced: %v", err)
	}
}
