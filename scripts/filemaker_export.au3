#include <Date.au3>

; Configuration
Global $FM_PATH = "C:\Program Files\FileMaker\FileMaker Pro 9\FileMaker Pro.exe"
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

; Launch FileMaker
Run($FM_PATH)
If @error Then
    MsgBox(16, "Error", "Could not launch FileMaker at:" & @CRLF & $FM_PATH)
    Exit
EndIf

MsgBox(0, "Status", "FileMaker launched. Click OK after FileMaker window appears.")

; Find FileMaker window - try different title patterns
Local $hwnd = 0
Local $winTitle = ""
Local $titles[3] = ["FileMaker Pro", "MAINPROEYE", "FileMaker"]
For $i = 0 To 2
    $hwnd = WinWait($titles[$i], "", 5)
    If $hwnd <> 0 Then
        $winTitle = $titles[$i]
        ExitLoop
    EndIf
Next

If $hwnd = 0 Then
    MsgBox(16, "Error", "Could not find FileMaker window. Please check if FileMaker is open.")
    Exit
EndIf

MsgBox(0, "Found", "Found window: " & $winTitle & @CRLF & "Handle: " & $hwnd)

WinActivate($hwnd)
Sleep(2000)

; Open with Shift+Enter for login
Send("+{ENTER}")
Sleep(3000)

; Enter credentials
Send($FM_LOGIN)
Sleep(200)
Send("{TAB}")
Sleep(200)
Send($FM_PASSWORD)
Sleep(200)
Send("{ENTER}")
Sleep(5000)

MsgBox(0, "Status", "Logged in. Click OK to continue to Menu.")

; Get window size using handle directly
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
