import { execFile } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, join } from "node:path";
import { promisify } from "node:util";

import * as vscode from "vscode";

const execFileAsync = promisify(execFile);

export function activate(context: vscode.ExtensionContext): void {
  const provider = vscode.languages.registerDocumentFormattingEditProvider("kaj", {
    provideDocumentFormattingEdits: formatDocument,
  });
  context.subscriptions.push(provider);
}

export function deactivate(): void {}

async function formatDocument(
  document: vscode.TextDocument,
  _options: vscode.FormattingOptions,
  token: vscode.CancellationToken,
): Promise<vscode.TextEdit[]> {
  if (document.isUntitled || document.isDirty) {
    void vscode.window.showWarningMessage(
      "Save the Kaj document before formatting. Unsaved buffers are not sent to kaj fmt.",
    );
    return [];
  }

  const executable = vscode.workspace
    .getConfiguration("kaj", document.uri)
    .get<string>("executablePath", "kaj")
    .trim();
  if (executable.length === 0) {
    void vscode.window.showErrorMessage(
      "Kaj formatter not found. Set kaj.executablePath or make kaj available on PATH.",
    );
    return [];
  }

  const directory = await mkdtemp(join(tmpdir(), "kaj-vscode-"));
  const temporaryPath = join(directory, basename(document.uri.fsPath));
  try {
    await writeFile(temporaryPath, document.getText(), "utf8");
    if (token.isCancellationRequested) {
      return [];
    }
    await execFileAsync(executable, ["fmt", temporaryPath], {
      encoding: "utf8",
      maxBuffer: 1024 * 1024,
      windowsHide: true,
    });
    if (token.isCancellationRequested) {
      return [];
    }
    const formatted = await readFile(temporaryPath, "utf8");
    if (formatted === document.getText()) {
      return [];
    }
    return [vscode.TextEdit.replace(fullDocumentRange(document), formatted)];
  } catch (error: unknown) {
    const details = formatterErrorMessage(error, executable);
    void vscode.window.showErrorMessage(details);
    return [];
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

function fullDocumentRange(document: vscode.TextDocument): vscode.Range {
  const lastLine = document.lineAt(document.lineCount - 1);
  return new vscode.Range(new vscode.Position(0, 0), lastLine.rangeIncludingLineBreak.end);
}

function formatterErrorMessage(error: unknown, executable: string): string {
  if (isNodeError(error) && error.code === "ENOENT") {
    return `Kaj formatter not found at '${executable}'. Set kaj.executablePath or make kaj available on PATH.`;
  }
  if (isExecError(error)) {
    const stderr = typeof error.stderr === "string" ? error.stderr.trim() : "";
    if (stderr.length > 0) {
      return `Kaj formatting failed: ${stderr}`;
    }
  }
  const message = error instanceof Error ? error.message : String(error);
  return `Kaj formatting failed: ${message}`;
}

function isNodeError(error: unknown): error is NodeJS.ErrnoException {
  return error instanceof Error && "code" in error;
}

function isExecError(error: unknown): error is Error & { stderr?: string } {
  return error instanceof Error && "stderr" in error;
}
