#include <Date.au3>

; Configuration
Global $FM_PATH = "C:\Program Files (x86)\FileMaker\FileMaker Pro 9\FileMaker Pro.exe"
Global $FM_DATABASE = "C:\1Program\Open.fp7"
Global $FM_LOGIN = "manager"
Global $FM_PASSWORD = "eynner"
Global $EXPORT_DIR = "C:\FilemakerRevEHR\exports"
Global $EXPORT_FILE = "monthly_report.pdf"

; Calculate previous month
Local $y = @YEAR
Local $m = @MON - 1
If $m = 0 Then
    $m = 12
    $y = $y - 1
EndIf
Local $days[13] = [0,31,28,31,30,31,30,31,31,30,31,30,31]
If $m = 2 And Mod($y, 4) = 0 Then $days[2] = 29
Local $dateRange = StringFormat("%02d/01/%04d...%02d/%02d/%04d", $m, $y, $m, $days[$m], $y)

; Create export dir
If Not FileExists($EXPORT_DIR) Then DirCreate($EXPORT_DIR)

; Launch FileMaker with database
Run($FM_PATH & ' "' & $FM_DATABASE & '"')
If @error Then Exit

; Wait for FileMaker to start
Sleep(8000)

; Look for any FileMaker window
Local $hwnd = 0
Local $winTitle = ""
Local $titles[5] = ["Open Password", "FileMaker Pro", "MAINPROEYE", "Open", "FileMaker"]
For $i = 0 To 4
    $hwnd = WinWait($titles[$i], "", 3)
    If $hwnd <> 0 Then
        $winTitle = $titles[$i]
        ExitLoop
    EndIf
Next

If $hwnd = 0 Then Exit

; Maximize the window
WinSetState($hwnd, "", @SW_MAXIMIZE)
Sleep(1000)
WinActivate($hwnd)
Sleep(500)

; Check if this is already a password dialog or need to trigger it
If Not StringInStr($winTitle, "Password") Then
    ; Try Shift+Enter to trigger login dialog
    Send("+{ENTER}")
    Sleep(3000)
    
    ; Wait for password dialog
    Local $pwdHwnd = WinWait("Open Password", "", 10)
    If $pwdHwnd = 0 Then
        $pwdHwnd = WinWait("Password", "", 5)
    EndIf
    If $pwdHwnd <> 0 Then
        WinActivate($pwdHwnd)
        $hwnd = $pwdHwnd
        Sleep(500)
    EndIf
EndIf

; Enter credentials - try clicking in the window first
WinActivate($hwnd)
Sleep(500)

; Get login dialog position and click in username field area
Local $aPos = WinGetPos($hwnd)
If IsArray($aPos) Then
    ; Click roughly in center of dialog where username field likely is
    MouseClick("left", $aPos[0] + ($aPos[2] / 2), $aPos[1] + ($aPos[3] / 2) - 20)
    Sleep(300)
EndIf

; Clear and type username
Send("^a")
Sleep(100)
Send($FM_LOGIN)
Sleep(300)
Send("{TAB}")
Sleep(200)
Send($FM_PASSWORD)
Sleep(300)
Send("{ENTER}")
Sleep(8000)

; Now find and maximize the main FileMaker window
$hwnd = 0
$titles[0] = "MAINPROEYE"
$titles[1] = "FileMaker Pro"
$titles[2] = "Open"
For $i = 0 To 2
    $hwnd = WinWait($titles[$i], "", 5)
    If $hwnd <> 0 Then
        $winTitle = $titles[$i]
        ExitLoop
    EndIf
Next

If $hwnd = 0 Then Exit

; Maximize main window
WinSetState($hwnd, "", @SW_MAXIMIZE)
Sleep(1000)
WinActivate($hwnd)
Sleep(1000)

; Get screen size (since maximized)
Local $screenW = @DesktopWidth
Local $screenH = @DesktopHeight

; Click Menu button (bottom-right area of maximized window)
; Adjust these coordinates based on your screen
MouseClick("left", $screenW - 150, $screenH - 150)
Sleep(2000)

; Click Internals button (center-lower area)
MouseClick("left", $screenW / 2, $screenH * 0.7)
Sleep(3000)

; Enter date range
Send("^a")
Sleep(200)
Send($dateRange)
Sleep(500)
Send("{ENTER}")
Sleep(3000)

; Click Month sort (top-right area)
MouseClick("left", $screenW - 200, 200)
Sleep(500)

; Click View button (top-right area)
MouseClick("left", $screenW - 100, 200)
Sleep(3000)

; Save as PDF: File menu
Send("!f")
Sleep(500)
Send("v")
Sleep(2000)

; Enter filename
Local $fullPath = $EXPORT_DIR & "\" & $EXPORT_FILE
Send($fullPath)
Sleep(500)
Send("{ENTER}")
Sleep(2000)
Send("{ENTER}")
Sleep(1000)

; Close FileMaker
Send("!{F4}")
Sleep(1000)
Send("{ENTER}")
