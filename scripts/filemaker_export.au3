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

; STEP 2: Login - just use keyboard, no clicking
Local $loginWin = WinWait("Open", "", 15)
If $loginWin <> 0 Then
    WinActivate($loginWin)
    Sleep(1000)
    
    ; Just type - assume username field has focus or tab to it
    Send($FM_LOGIN)
    Sleep(300)
    Send("{TAB}")
    Sleep(200)
    Send($FM_PASSWORD)
    Sleep(300)
    Send("{ENTER}")
    Sleep(5000)
EndIf

; STEP 3: After login - MAXIMIZE the main window for consistent coordinates
Local $mainWin = WinWait("FileMaker Pro", "", 10)
If $mainWin = 0 Then
    $mainWin = WinWait("Patients", "", 5)
EndIf
If $mainWin = 0 Then
    $mainWin = WinWait("[CLASS:FM9_HostWindow]", "", 5)
EndIf

If $mainWin <> 0 Then
    WinActivate($mainWin)
    WinSetState($mainWin, "", @SW_MAXIMIZE)
    Sleep(2000)
    
    ; On maximized 2560x1080, the teal content area is fixed size
    ; Teal area is approximately 460x370 pixels, positioned in upper-left
    ; Content starts after ~45px left margin and ~80px top (toolbar)
    
    ; Reports Menu button (green) - in Reports section
    ; Approximately x=255, y=270 from top-left of screen when maximized
    MouseClick("left", 255, 270)
    Sleep(2000)
EndIf

; STEP 4: Business Reports - Click LOWER Internals button
Sleep(1000)
; Lower Internals button approximately x=235, y=310
MouseClick("left", 235, 310)
Sleep(3000)

; STEP 5: Report Setup - Enter date range
; Date field is in center-upper area of teal content
; Approximately x=290, y=205
MouseClick("left", 290, 205)
Sleep(300)
Send("^a")
Sleep(100)
Send($dateRange)
Sleep(500)

; Click Continue button (left side, in the left panel area)
; Approximately x=55, y=305
MouseClick("left", 55, 305)
Sleep(5000)

; STEP 6: Internals Report - Click Month button, then View
; Month button in top-right button group, approximately x=665, y=155
MouseClick("left", 665, 155)
Sleep(1000)

; View button (green) approximately x=750, y=140
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

; Close FileMaker
Send("!{F4}")
Sleep(1000)
Send("n")
Sleep(500)
