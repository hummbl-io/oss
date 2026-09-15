#!/usr/bin/env node

import { createInterface } from "node:readline";

import { createRequestHandler } from "../src/server.mjs";

const handleRequest = createRequestHandler();

const lines = createInterface({ input: process.stdin, crlfDelay: Infinity, terminal: false });

for await (const line of lines) {
  if (!line.trim()) continue;
  let response;
  try {
    response = await handleRequest(JSON.parse(line));
  } catch {
    response = {
      jsonrpc: "2.0",
      id: null,
      error: {
        code: -32700,
        message: "Parse error",
      },
    };
  }
  if (response !== undefined) process.stdout.write(`${JSON.stringify(response)}\n`);
}
