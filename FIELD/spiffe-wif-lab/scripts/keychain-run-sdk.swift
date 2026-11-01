import Foundation
import LocalAuthentication
import Security

// macOS host launcher. The key is read into memory from Keychain and given only
// to the host-side SDK process over a local pipe. It never enters a CLI
// argument, process environment, env file, Docker service or evidence file.
let service = ProcessInfo.processInfo.environment["FIELDDESK_KEYCHAIN_SERVICE"]
    ?? "com.mathborgess.red-blue-field.openai-api-key"
let account = ProcessInfo.processInfo.environment["FIELDDESK_KEYCHAIN_ACCOUNT"]
    ?? NSUserName()
let context = LAContext()
context.interactionNotAllowed = true
let query: [String: Any] = [
    kSecClass as String: kSecClassGenericPassword,
    kSecAttrService as String: service,
    kSecAttrAccount as String: account,
    kSecReturnData as String: true,
    kSecMatchLimit as String: kSecMatchLimitOne,
    kSecUseAuthenticationContext as String: context,
]
var result: CFTypeRef?
let status = SecItemCopyMatching(query as CFDictionary, &result)
guard status == errSecSuccess,
      let data = result as? Data,
      let key = String(data: data, encoding: .utf8),
      key.hasPrefix("sk-"), key.count > 30 else {
    fputs("OpenAI key unavailable in Keychain (status \(status)).\n", stderr)
    exit(1)
}

let labDirectory = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
let python = labDirectory.appendingPathComponent("state/.venv-agents/bin/python")
let driver = labDirectory.appendingPathComponent("sdk_driver.py")
guard FileManager.default.isExecutableFile(atPath: python.path) else {
    fputs("Install requirements-agents.txt into state/.venv-agents first.\n", stderr)
    exit(1)
}

var environment = ProcessInfo.processInfo.environment
environment.removeValue(forKey: "OPENAI_API_KEY")
environment["FIELDDESK_KEY_STDIN"] = "1"
let child = Process()
child.executableURL = python
child.arguments = [driver.path] + Array(CommandLine.arguments.dropFirst())
child.environment = environment
let input = Pipe()
child.standardInput = input
child.standardOutput = FileHandle.standardOutput
child.standardError = FileHandle.standardError
do {
    try child.run()
    try input.fileHandleForWriting.write(contentsOf: Data((key + "\n").utf8))
    try input.fileHandleForWriting.close()
    child.waitUntilExit()
    exit(child.terminationStatus)
} catch {
    fputs("Could not start the Agents SDK driver.\n", stderr)
    exit(1)
}
