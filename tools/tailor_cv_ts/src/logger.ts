type Level = "debug" | "info" | "success" | "warning" | "error";

const COLORS: Record<Level, string> = {
  debug:   "\x1b[36m",
  info:    "\x1b[34m",
  success: "\x1b[32m",
  warning: "\x1b[33m",
  error:   "\x1b[31m",
};
const RESET = "\x1b[0m";
const ORDER: Record<Level, number> = { debug: 0, info: 1, success: 2, warning: 3, error: 4 };

let currentLevel: Level = "info";

export function setLogLevel(level: string): void {
  currentLevel = level.toLowerCase() as Level;
}

function log(level: Level, message: string): void {
  if (ORDER[level] < ORDER[currentLevel]) return;
  const time = new Date().toISOString().split("T")[1].split(".")[0];
  process.stderr.write(`${COLORS[level]}${time} ${level.toUpperCase().padEnd(7)} ${message}${RESET}\n`);
}

export const logger = {
  debug:   (msg: string) => log("debug",   msg),
  info:    (msg: string) => log("info",    msg),
  success: (msg: string) => log("success", msg),
  warning: (msg: string) => log("warning", msg),
  error:   (msg: string) => log("error",   msg),
};
