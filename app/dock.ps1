# app/dock.ps1 - waits for the FixPilot panel window and docks it on the right edge of the primary screen.
param([int]$Width = 460)
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
public class FpDock {
 public delegate bool EnumProc(IntPtr h, IntPtr l);
 [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc p, IntPtr l);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int cx, int cy, uint f);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 public static IntPtr Found = IntPtr.Zero;
 public static void Find(string title) { Found = IntPtr.Zero; EnumWindows((h,l)=>{ if(!IsWindowVisible(h)) return true; var sb=new StringBuilder(256); GetWindowText(h,sb,256); if(sb.ToString()==title){ Found=h; return false;} return true; }, IntPtr.Zero); }
}
"@
[FpDock]::SetProcessDPIAware() | Out-Null
$area = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea   # excludes the taskbar
for ($i = 0; $i -lt 40; $i++) {
    [FpDock]::Find("FixPilot")
    if ([FpDock]::Found -ne [IntPtr]::Zero) {
        [FpDock]::ShowWindow([FpDock]::Found, 9) | Out-Null   # restore if minimized/maximized
        [FpDock]::SetWindowPos([FpDock]::Found, [IntPtr]::Zero, $area.Right - $Width, $area.Top, $Width, $area.Height, 0x0040) | Out-Null
        exit 0
    }
    Start-Sleep -Milliseconds 250
}
Write-Host "FixPilot window not found (it may still be loading)."
