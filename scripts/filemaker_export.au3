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
Sleep(8000)

; STEP 1: Handle Quick Start dialog if it appears
Local $quickStart = WinWait("FileMaker Quick Start", "", 5)
If $quickStart <> 0 Then
    WinActivate($quickStart)
    Sleep(500)
    Local $qsPos = WinGetPos($quickStart)
    If IsArray($qsPos) Then
        MouseClick("left", $qsPos[0] + 250, $qsPos[1] + 180, 2)
    EndIf
    Sleep(3000)
EndIf

; STEP 2: Login - password field is focused first
Local $loginWin = WinWait("Open", "", 15)
If $loginWin <> 0 Then
    WinActivate($loginWin)
    Sleep(1000)
    
    ; Password field is focused first
    Send($FM_PASSWORD)
    Sleep(300)
    ; Tab 5 times to get to username field
    Send("{TAB}{TAB}{TAB}{TAB}{TAB}")
    Sleep(300)
    Send($FM_LOGIN)
    Sleep(300)
    Send("{ENTER}")
    Sleep(5000)
EndIf

; STEP 3: After login - MAXIMIZE for consistent coordinates
Local $mainWin = WinWait("FileMaker Pro", "", 10)
If $mainWin = 0 Then
    $mainWin = WinWait("Patients", "", 5)
EndIf

If $mainWin <> 0 Then
    WinActivate($mainWin)
    WinSetState($mainWin, "", @SW_MAXIMIZE)
    Sleep(2000)
    
    ; Reports Menu button (green) - in Reports section
    MouseClick("left", 255, 270)
    Sleep(2000)
EndIf

; STEP 4: Business Reports - Click LOWER Internals button
Sleep(1000)
MouseClick("left", 235, 310)
Sleep(3000)

; STEP 5: Report Setup - Enter date range
MouseClick("left", 290, 205)
Sleep(300)
Send("^a")
Sleep(100)
Send($dateRange)
Sleep(500)

; Click Continue button
MouseClick("left", 55, 305)
Sleep(5000)

; STEP 6: Internals Report - Click Month button, then View
MouseClick("left", 665, 155)
Sleep(1000)
MouseClick("left", 750, 140)
Sleep(3000)

; STEP 7: Save as PDF
Send("!f")
Sleep(500)
Send("v")
Sleep(2000)

Local $fullPath = $EXPORT_DIR & "\" & $EXPORT_FILE
Send($fullPath)
Sleep(500)
Send("{ENTER}")
Sleep(2000)
Send("{ENTER}")
Sleep(1000)

; STEP 8: Snap window to left half of screen (Win + Left Arrow)
Send("#Left")
Sleep(500)
