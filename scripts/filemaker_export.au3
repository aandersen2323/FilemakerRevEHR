#include <Date.au3>

; Configuration
Global $FM_PATH = "C:\Program Files\FileMaker\FileMaker Pro 9\FileMaker Pro.exe"
Global $FM_WINDOW = "FileMaker Pro"
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
Sleep(5000)

; Wait for FileMaker window
WinWait($FM_WINDOW, "", 30)
WinActivate($FM_WINDOW)
WinWaitActive($FM_WINDOW, "", 10)
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

; Get window position
Local $pos = WinGetPos($FM_WINDOW)
If @error Then
    MsgBox(0, "Error", "Could not find FileMaker window")
    Exit
EndIf
Local $winW = $pos[2]
Local $winH = $pos[3]
Local $winX = $pos[0]
Local $winY = $pos[1]

; Click Menu button (bottom-right area)
MouseClick("left", $winX + $winW - 150, $winY + $winH - 100)
Sleep(2000)

; Click lower Internals button (center-lower area)
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

MsgBox(0, "Done", "PDF exported to: " & $fullPath)
