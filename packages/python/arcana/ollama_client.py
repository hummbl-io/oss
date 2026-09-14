import json
import sys
import urllib.error
import urllib.request

from .api_client import AgentGenerationRequest, GenerationResult, SynthesisRequest


class OllamaAPIClient:
    def __init__(self, model_name='qwen3.5:9b', base_url='http://localhost:11434/api/generate'):
        self.model_name = model_name
        self.base_url = base_url

    def _call_ollama(self, prompt, system_prompt=None):
        payload = {
            'model': self.model_name,
            'prompt': prompt,
            'stream': False,
            'format': 'json'
        }
        if system_prompt:
            payload['system'] = system_prompt

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(self.base_url, data=data, headers={'Content-Type': 'application/json'})
        
        try:
            with urllib.request.urlopen(req) as response:
                raw_res = response.read().decode('utf-8')
                res_data = json.loads(raw_res)
                
                # Debug log to stderr
                # print(f"DEBUG: Ollama response: {raw_res}", file=sys.stderr)
                
                content = res_data.get('response', '')
                
                return GenerationResult(
                    content=content,
                    model=self.model_name,
                    usage={
                        'prompt_tokens': res_data.get('prompt_eval_count', 0),
                        'completion_tokens': res_data.get('eval_count', 0),
                        'total_tokens': res_data.get('prompt_eval_count', 0) + res_data.get('eval_count', 0)
                    }
                )
        except Exception as e:
            print(f"ERROR calling Ollama: {e}", file=sys.stderr)
            return GenerationResult(content=json.dumps({'error': str(e)}), model=self.model_name)

    def generate_perspective(self, request: AgentGenerationRequest) -> GenerationResult:
        prompt = f"Analyze the topic: '{request.topic}' from your perspective as {request.agent_name} ({request.lens}). Return a JSON object with 'perspective', 'key_claims' (list), and 'blind_spots'."
        return self._call_ollama(prompt, system_prompt=request.system_prompt)

    def generate_synthesis(self, request: SynthesisRequest) -> GenerationResult:
        perspectives_str = '\n\n'.join([f"Agent: {p.agent_name}\nPerspective: {p.perspective}" for p in request.perspectives])
        prompt = f"Synthesize the following perspectives on '{request.topic}':\n\n{perspectives_str}\n\nReturn a JSON object with 'title', 'summary', 'convergences' (list), 'divergences' (list), 'synthesis' (full essay), 'live_questions' (list), 'tags' (list), and 'confidence_score' (0-1)."
        return self._call_ollama(prompt, system_prompt=request.system_prompt)
