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

MsgBox(0, "Monthly Report Export", "Will export: " & $dateRange & @CRLF & @CRLF & "Click OK to start. Make sure FileMaker is closed.")

; Create export dir
If Not FileExists($EXPORT_DIR) Then DirCreate($EXPORT_DIR)

; Launch FileMaker with database
Run($FM_PATH & ' "' & $FM_DATABASE & '"')
If @error Then
    MsgBox(16, "Error", "Could not launch FileMaker at:" & @CRLF & $FM_PATH)
    Exit
EndIf

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

If $hwnd = 0 Then
    MsgBox(16, "Error", "Could not find FileMaker window.")
    Exit
EndIf

MsgBox(0, "Found", "Found window: " & $winTitle)

; Check if this is already a password dialog
If StringInStr($winTitle, "Password") Then
    ; Already at login dialog
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

MsgBox(0, "Login", "About to enter credentials. Click OK.")

; Click in the username field first to make sure it's focused
Sleep(500)
Send("{TAB}{TAB}{TAB}")  ; Tab through to get to username field
Sleep(200)
Send("^a")  ; Select all in case there's existing text
Sleep(100)
Send($FM_LOGIN)
Sleep(300)
Send("{TAB}")
Sleep(200)
Send($FM_PASSWORD)
Sleep(300)

MsgBox(0, "Credentials", "Entered: " & $FM_LOGIN & " / " & $FM_PASSWORD & @CRLF & "Click OK to press Enter")

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

If $hwnd = 0 Then
    MsgBox(16, "Error", "Could not find main window after login.")
    Exit
EndIf

MsgBox(0, "Status", "Logged in. Main window: " & $winTitle & @CRLF & "Click OK to continue to Menu.")

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
    MsgBox(0, "Window", "Position: " & $winX & "," & $winY & @CRLF & "Size: " & $winW & "x" & $winH)
Else
    MsgBox(48, "Warning", "Could not get window position, using defaults")
EndIf

; Click Menu button (bottom-right area)
Local $menuX = $winX + $winW - 150
Local $menuY = $winY + $winH - 100
MsgBox(0, "Click", "Will click Menu at: " & $menuX & "," & $menuY & @CRLF & "Click OK to proceed")
MouseClick("left", $menuX, $menuY)
Sleep(2000)

; Click Internals button (center-lower area)
Local $intX = $winX + ($winW / 2)
Local $intY = $winY + ($winH * 0.7)
MsgBox(0, "Click", "Will click Internals at: " & $intX & "," & $intY & @CRLF & "Click OK to proceed")
MouseClick("left", $intX, $intY)
Sleep(3000)

; Enter date range
Send("^a")
Sleep(200)
Send($dateRange)
Sleep(500)
Send("{ENTER}")
Sleep(3000)

; Click Month sort (top-right)
Local $sortX = $winX + $winW - 200
Local $sortY = $winY + 150
MsgBox(0, "Click", "Will click Month sort at: " & $sortX & "," & $sortY & @CRLF & "Click OK to proceed")
MouseClick("left", $sortX, $sortY)
Sleep(500)

; Click View button (top-right)
Local $viewX = $winX + $winW - 100
Local $viewY = $winY + 150
MsgBox(0, "Click", "Will click View at: " & $viewX & "," & $viewY & @CRLF & "Click OK to proceed")
MouseClick("left", $viewX, $viewY)
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

MsgBox(0, "Done", "PDF exported to: " & $fullPath)
