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
    const projectRoot = "/Users/harshabajaj/Desktop/HACKATHON1/code-mentor";
    const outputPath = path.join(projectRoot, "chunks", `${workspaceName}_chunks.json`);

    // Ensure chunks directory exists
    await fs.promises.mkdir(path.join(projectRoot, "chunks"), { recursive: true });

    const chunkPythonScript = path.join("/Users/harshabajaj/Desktop/HACKATHON1/code-mentor/src", "code_chunker.py");
    const markdownPythonScript = path.join("/Users/harshabajaj/Desktop/HACKATHON1/code-mentor/src", "markdown_generator.py");
    const requirementsFile = path.join("/Users/harshabajaj/Desktop/HACKATHON1/code-mentor", "requirements.txt");

    exec(`python3 -m pip install --upgrade pip`, (error, stdout, stderr) => {
        if (error) {
            vscode.window.showErrorMessage(`Failed to install pip: ${error.message}`);
            return;
        }
        if (stderr) {
            vscode.window.showWarningMessage(`Dependency installation warnings: ${stderr}`);
        }
    });
    
    return new Promise((resolve, reject) => {
        exec(`pip3 install -r "${requirementsFile}"`, (error, stdout, stderr) => {
            if (error) {
                vscode.window.showErrorMessage(`Failed to install dependencies: ${error.message}`);
                reject(error);
                return;
            }
            if (stderr) {
                vscode.window.showWarningMessage(`Dependency installation warnings: ${stderr}`);
            }

            // Run the Python scripts
            exec(`python3 "${markdownPythonScript}" "${workspacePath}"`, (error, stdout, stderr) => {
                if (error) {
                    vscode.window.showErrorMessage(`Markdown generation failed: ${error.message}`);
                    reject(error);
                    return;
                }
                if (stderr) {
                    vscode.window.showWarningMessage(`Markdown generation warnings: ${stderr}`);
                }
                vscode.window.showInformationMessage("Markdown file generated successfully!");
            });

            exec(`python3 "${chunkPythonScript}" "${workspacePath}"`, (error, stdout, stderr) => {
                if (error) {
                    vscode.window.showErrorMessage(`Chunking failed: ${error.message}`);
                    reject(error);
                    return;
                }
                if (stderr) {
                    vscode.window.showWarningMessage(`Chunking warnings: ${stderr}`);
                }
                vscode.window.showInformationMessage("Code chunks generated successfully!");
                resolve({
                    chunksPath: outputPath,
                    workspaceName,
                    email,
                    firstFlag
                });
            });
        });
    });
}