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
Sleep(5000)

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

; Check if this is already a password dialog
If StringInStr($winTitle, "Password") Then
    WinActivate($hwnd)
    Sleep(500)
Else
    ; Need to trigger login dialog with Shift+Enter
    WinActivate($hwnd)
    Sleep(1000)
    Send("+{ENTER}")
    Sleep(2000)
    
    ; Wait for password dialog
    Local $pwdHwnd = WinWait("Open Password", "", 10)
    If $pwdHwnd = 0 Then
        $pwdHwnd = WinWait("Password", "", 5)
    EndIf
    If $pwdHwnd <> 0 Then
        WinActivate($pwdHwnd)
        Sleep(500)
    EndIf
EndIf

; Enter credentials
Sleep(500)
Send("{TAB}{TAB}{TAB}")
Sleep(200)
Send("^a")
Sleep(100)
Send($FM_LOGIN)
Sleep(300)
Send("{TAB}")
Sleep(200)
Send($FM_PASSWORD)
Sleep(300)
Send("{ENTER}")
Sleep(5000)

; Now find the main FileMaker window
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

WinActivate($hwnd)
Sleep(1000)

; Get window position
Local $winW = 1024
Local $winH = 768
Local $winX = 0
Local $winY = 0

Local $aPos = WinGetPos($hwnd)
If IsArray($aPos) Then
    $winX = $aPos[0]
    $winY = $aPos[1]
    $winW = $aPos[2]
    $winH = $aPos[3]
EndIf

; Click Menu button (bottom-right area)
MouseClick("left", $winX + $winW - 150, $winY + $winH - 100)
Sleep(2000)

; Click Internals button (center-lower area)
MouseClick("left", $winX + ($winW / 2), $winY + ($winH * 0.7))
Sleep(3000)

; Enter date range
Send("^a")
Sleep(200)
Send($dateRange)
Sleep(500)
Send("{ENTER}")
Sleep(3000)

; Click Month sort (top-right)
MouseClick("left", $winX + $winW - 200, $winY + 150)
Sleep(500)

; Click View button (top-right)
MouseClick("left", $winX + $winW - 100, $winY + 150)
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
