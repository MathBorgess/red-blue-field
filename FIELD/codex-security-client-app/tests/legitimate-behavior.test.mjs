import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import test from "node:test";

const require = createRequire(import.meta.url);
const utils = require("../utils.js");

test("uid returns the requested number of portable characters", () => {
  const value = utils.uid(24);
  assert.equal(value.length, 24);
  assert.match(value, /^[A-Za-z0-9]+$/);
});

test("forbidden returns the established plain-text response", () => {
  const headers = new Map();
  let body;
  const response = {
    statusCode: 0,
    setHeader(name, value) {
      headers.set(name.toLowerCase(), value);
    },
    end(value) {
      body = value;
    },
  };

  utils.forbidden(response);

  assert.equal(response.statusCode, 403);
  assert.equal(headers.get("content-type"), "text/plain");
  assert.equal(headers.get("content-length"), "Forbidden".length);
  assert.equal(body, "Forbidden");
});

test("task creation, import, and account routes remain registered", async () => {
  const appSource = await readFile(new URL("../app.js", import.meta.url), "utf8");
  assert.match(appSource, /app\.post\('\/create',\s*(?:[\w$.]+\s*,\s*)*routes\.create\)/);
  assert.match(appSource, /app\.post\('\/import',\s*(?:[\w$.]+\s*,\s*)*routes\.import\)/);
  assert.match(appSource, /app\.post\('\/account_details', routes\.isLoggedIn, routes\.save_account_details\)/);
});

test("the primary task form still submits content to the create route", async () => {
  const view = await readFile(new URL("../views/index.ejs", import.meta.url), "utf8");
  assert.match(view, /<form action="\/create" method="post"/);
  assert.match(view, /<input class="input" type="text" name="content"/);
});
