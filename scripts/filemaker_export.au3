#include <Date.au3>

; Configuration
Global $FM_PATH = "C:\Program Files (x86)\FileMaker\FileMaker Pro 9\FileMaker Pro.exe"
Global $FM_DATABASE = "C:\1Program\Open.fp7"
Global $FM_LOGIN = "manager"
Global $FM_PASSWORD = "eynner"
Global $EXPORT_DIR = "C:\FilemakerRevEHR\exports"
Global $EXPORT_FILE = "monthly_report.pdf"

; Screen resolution: 2560x1080
Global $SCREEN_W = 2560
Global $SCREEN_H = 1080

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
        ; Double-click on "Open-MAINPROEYE" in recent files list
        MouseClick("left", $qsPos[0] + 250, $qsPos[1] + 180, 2)
    EndIf
    Sleep(3000)
EndIf

; STEP 2: Handle Login dialog
Local $loginWin = WinWait("Open", "Account", 10)
If $loginWin = 0 Then
    $loginWin = WinWait("Open", "Password", 10)
EndIf

If $loginWin <> 0 Then
    WinActivate($loginWin)
    Sleep(500)
    
    Local $loginPos = WinGetPos($loginWin)
    If IsArray($loginPos) Then
        ; Click in the Account Name field (center of dialog)
        MouseClick("left", $loginPos[0] + ($loginPos[2] / 2), $loginPos[1] + ($loginPos[3] / 2) - 30)
        Sleep(200)
    EndIf
    
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
EndIf

; STEP 3: Main Menu - Find window and click Reports Menu (green)
Local $mainWin = WinWait("FileMaker Pro", "", 10)
If $mainWin = 0 Then
    $mainWin = WinWait("Patients", "", 5)
EndIf

If $mainWin <> 0 Then
    WinActivate($mainWin)
    Sleep(500)
    
    ; Get window position - don't maximize, work with natural size
    Local $winPos = WinGetPos($mainWin)
    If IsArray($winPos) Then
        ; FileMaker teal content area starts ~45px from left, ~80px from top
        ; Reports Menu button (green) is in the teal area at approximately:
        ; x=210 from teal left, y=190 from teal top
        Local $tealX = $winPos[0] + 45
        Local $tealY = $winPos[1] + 80
        
        ; Click Reports Menu button (green)
        MouseClick("left", $tealX + 210, $tealY + 190)
        Sleep(2000)
    EndIf
EndIf

; STEP 4: Business Reports - Click LOWER Internals button (yellow)
Sleep(1000)
$mainWin = WinGetHandle("[ACTIVE]")
Local $winPos = WinGetPos($mainWin)
If IsArray($winPos) Then
    Local $tealX = $winPos[0] + 45
    Local $tealY = $winPos[1] + 80
    
    ; Lower Internals button is at approximately x=190, y=230 in teal area
    MouseClick("left", $tealX + 190, $tealY + 230)
    Sleep(3000)
EndIf

; STEP 5: Report Setup - Enter date range and click Continue
Sleep(1000)
$winPos = WinGetPos("[ACTIVE]")
If IsArray($winPos) Then
    Local $tealX = $winPos[0] + 45
    Local $tealY = $winPos[1] + 80
    
    ; Click in date field (center of teal area, upper portion)
    MouseClick("left", $tealX + 220, $tealY + 75)
    Sleep(300)
EndIf

Send("^a")
Sleep(100)
Send($dateRange)
Sleep(500)

; Click Continue button (left side of teal area)
$winPos = WinGetPos("[ACTIVE]")
If IsArray($winPos) Then
    Local $tealX = $winPos[0] + 45
    Local $tealY = $winPos[1] + 80
    MouseClick("left", $tealX - 25, $tealY + 200)
EndIf
Sleep(5000)

; STEP 6: Internals Report - Click Month button, then View
$winPos = WinGetPos("[ACTIVE]")
If IsArray($winPos) Then
    ; Month and View buttons are in top-right area
    ; For the Internals report view, buttons are further right
    Local $btnAreaX = $winPos[0] + $winPos[2] - 200
    Local $btnAreaY = $winPos[1] + 100
    
    ; Month button
    MouseClick("left", $btnAreaX + 30, $btnAreaY)
    Sleep(1000)
    
    ; View button (to the right of Month)
    MouseClick("left", $btnAreaX + 100, $btnAreaY - 20)
    Sleep(3000)
EndIf

; STEP 7: Save as PDF from Preview
Send("!f")
Sleep(500)
Send("v")
Sleep(2000)

; Save dialog
Local $saveWin = WinWait("Save", "", 5)
If $saveWin <> 0 Then
    WinActivate($saveWin)
    Sleep(500)
EndIf

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
