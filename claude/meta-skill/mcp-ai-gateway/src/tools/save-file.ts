import { writeFile, mkdir } from "node:fs/promises";
import { existsSync, realpathSync } from "node:fs";
import { dirname, resolve, sep } from "node:path";

// Generated media is written for the caller, so the caller names the path — but only
// inside the project the gateway was started in (or AI_GATEWAY_SAVE_ROOT when set).
function saveRoot(): string {
  return realpathSync(process.env.AI_GATEWAY_SAVE_ROOT || process.cwd());
}

export function checkSavePath(savePath: string): string {
  const root = saveRoot();
  const target = resolve(root, savePath);
  // A symlinked directory can leave the root, so judge the nearest existing ancestor.
  let existing = dirname(target);
  while (!existsSync(existing)) existing = dirname(existing);
  const real = realpathSync(existing);
  if (real !== root && !real.startsWith(root + sep)) {
    throw new Error(`save_path must stay inside ${root}: ${savePath}`);
  }
  if (target !== root && !target.startsWith(root + sep)) {
    throw new Error(`save_path must stay inside ${root}: ${savePath}`);
  }
  return target;
}

export async function saveFile(savePath: string, data: Buffer): Promise<void> {
  const target = checkSavePath(savePath);
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, data);
}
