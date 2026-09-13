import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync(new URL("../src/ideenschmiede/api.ts", import.meta.url), "utf8");

// Jeder Ideenschmiede-Endpunkt muss über den Vite-Proxy zum Backend gehen.
// Ein fehlendes /api führt stattdessen zu einem 404 aus dem Frontend-Server.
const direkteFehlpfade = source
  .split("\n")
  .filter((zeile) => zeile.includes("`${campaignId}") && zeile.includes("/campaigns/"));

assert.deepEqual(
  direkteFehlpfade,
  [],
  `Ideenschmiede verwendet Frontend-Pfade ohne /api:\n${direkteFehlpfade.join("\n")}`,
);

assert.match(source, /\/api\/campaigns\/\$\{campaignId\}/, "Es muss einen /api/campaigns-Pfad geben.");
console.log("Ideenschmiede-API-Pfade sind korrekt präfixiert.");
