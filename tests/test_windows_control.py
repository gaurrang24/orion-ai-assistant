from tools.windows_control import WindowsControlTool


print("Testing Windows Control Tool")

# Test screenshot
path = WindowsControlTool.screenshot()

if path:
    print(f"Screenshot created: {path}")
else:
    print("Screenshot failed")