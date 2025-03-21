import { exec } from "child_process";
import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";

export async function generateCodeChunks(email: string, firstFlag: boolean) {
    console.log("Generating code chunks...");
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
        vscode.window.showErrorMessage("No workspace is open!");
        return;
    }

    const workspacePath = workspaceFolders[0].uri.fsPath;
    const workspaceName = workspaceFolders[0].name;
    const projectRoot = "/Users/harshabajaj/Desktop/HACKATHON1/testing/code-mentor-team-1/frontend";
    const pythonScript = path.join(projectRoot, "src", "code_chunker.py");
    
    // Define output path in your local folder
    const outputPath = path.join(projectRoot, "chunks", `${workspaceName}_chunks.json`);
    
    // Ensure chunks directory exists
    await fs.promises.mkdir(path.join(projectRoot, "chunks"), { recursive: true });
    
    const venvPath = path.join(projectRoot, "venv");
    const pythonExecutable = path.join(venvPath, "bin", "python");

    return new Promise((resolve, reject) => {
        exec(
            `"${pythonExecutable}" "${pythonScript}" "${workspacePath}" "${outputPath}"`,
            async (error, stdout, stderr) => {
                console.log("Chunking output: ", stdout);
                
                if (error) {
                    vscode.window.showErrorMessage(`Chunking failed: ${error.message}`);
                    reject(error);
                    return;
                }
                
                if (stderr) {
                    console.log("Chunking stderr: ", stderr);
                    vscode.window.showWarningMessage(`Chunking warnings: ${stderr}`);
                }
                
                vscode.window.showInformationMessage("Code chunks generated successfully!");
                resolve({
                    chunksPath: outputPath,
                    workspaceName,
                    email,
                    firstFlag
                });
            }
        );
    });
}