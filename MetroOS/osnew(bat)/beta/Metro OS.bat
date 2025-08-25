@echo off
color 1f


:bootmenu
color 1f
cls 
echo ======================================================
echo                      BOOT MENU
echo                     cmd support
echo ======================================================
echo 1. sign in
echo 2. system setting
echo 3. exit
set /p choice=Enter your choice here: 
if "%choice%"=="1" goto system
if "%choice%"=="2" goto setting
if "%choice%"=="3" goto exit
if "%choice%"=="dirdev" goto devtoolc


:system 
color f0
cls
echo ======================================================
echo                   WELCOME TO METRO OS	
echo                      DOS support 
echo ======================================================
echo. 
echo 1. File Manager
echo 2. Clock
echo 3. News
echo 4. Calculator
echo 5. system imformation
echo 6. password manager
echo 7. restart
echo 8. shutdown
echo 9. Back to Boot Menu
set /p syschoice=Enter your choice here: 

if "%syschoice%"=="1" goto filemanager
if "%syschoice%"=="2" goto clock 
if "%syschoice%"=="3" goto news 
if "%syschoice%"=="4" goto calculator 
if "%syschoice%"=="5" goto sysimformation
if "%syschoice%"=="6" goto passmanager
if "%syschoice%"=="7" goto restart
if "%syschoice%"=="8" goto exit 
if "%syschoice%"=="9" goto bootmenu


:filemanager
set "root=%~dp0G"
if not exist "%root%" mkdir "%root%"
cd /d "%root%"
cls
echo ======================================================
echo                     FILE MANAGER 
echo             yoh let make someting good
echo ======================================================
echo 1. Create Folder
echo 2. Create File
echo 3. Delete File/Folder
echo 4. Open File
echo 5. Change Directory
echo 6. Go to G:
echo 7. See local disk and files
echo 8. Exit
echo ======================================================
set /p choice=Enter your choice: 

if "%choice%"=="1" goto create_folder
if "%choice%"=="2" goto create_file
if "%choice%"=="3" goto delete
if "%choice%"=="4" goto open_file
if "%choice%"=="5" goto change_dir
if "%choice%"=="6" cd /d "%root%" && goto filemanager
if "%choice%"=="7" goto filesee
if "%choice%"=="8" goto system
goto filemanager

:create_folder
set /p foldername=Enter folder name: 
mkdir "%foldername%" && echo Folder "%foldername%" created!
pause
goto filemanager

:create_file
set /p filename=Enter file name: 
type nul > "%filename%" && echo File "%filename%" created!
pause
goto filemanager

:delete
set /p target=Enter file/folder to delete: 
if exist "%target%" (rmdir /s /q "%target%" 2>nul || del /f /q "%target%") && echo "%target%" deleted!
pause
goto filemanager

:open_file
set /p filename=Enter file name: 
if exist "%filename%" (more "%filename%" 2>nul || start "" "%filename%") else echo File not found!
pause
goto filemanager

:change_dir
set /p foldername=Enter folder name: 
if exist "%foldername%" (
    cd /d "%foldername%"
    echo Entered "%foldername%"!
) else (
    echo Folder "%foldername%" not found!
)
pause
goto filemanager

:filesee
cls
echo ======================================================
echo                  LIST OF FILES & FOLDERS               
echo ======================================================
echo.
echo [Folders:]
for /d %%D in (*) do echo %%D
echo.
echo [Files:]
for %%i in (*) do if not "%%i"=="desktop.ini" echo %%i
echo ======================================================
pause
goto filemanager


:news
cls
echo ======================================================
echo                    NEWS READER
echo ======================================================
set "newsPath=%~dp0G\News"
if not exist "%newsPath%" mkdir "%newsPath%"

echo Available News Files:
dir /b "%newsPath%\*.txt" 2>nul || echo No news available.

echo ======================================================
set /p filename=Enter the news file name (or type "exit" to return): 

if /i "%filename%"=="exit" goto news
if exist "%newsPath%\%filename%" (
    cls
    echo ======================================================
    echo                      NEWS
    echo ======================================================
    type "%newsPath%\%filename%"
    echo.
    echo ======================================================
) else (
    echo Error: File not found!
)

pause
goto news


:calculator
cls
color 0E
echo ======================================================
echo                      CALCULATOR
echo     Enter an expression (e.g., 3+3 or 5*8 or 10/2)
echo          Type '1' to restart or '2' to quit.
echo ======================================================
set /p expression=Enter calculation: 

if /i "%expression%"=="1" goto system 
if /i "%expression%"=="2" goto calculator

echo %expression% | findstr /r "\/0" >nul && goto scary_error

set /a result=%expression% 2>nul

if "%result%"=="" (
    echo Invalid input! Please enter a valid expression.
) else (
    echo %expression% = %result%
)

pause
goto calculator

:scary_error
cls
color 47
echo ======================================================
echo                   !!! ERROR !!!
echo     SYSTEM INSTABILITY DETECTED! CODE: 0xDEAD0000
echo          FATAL EXCEPTION IN PROCESSOR CORE
echo ======================================================
echo Press Enter to recover...
echo.

:loop
echo ERROR DETECTED! SYSTEM FAILURE! WARNING!!! %random%
timeout /t 0 >nul
goto check_input

:check_input
set /p stop=
if not "%stop%"=="" goto calculator
goto loop



:clock 
color f0
cls
echo ======================================================
echo                         CLOCK 
echo             tic tac tic tac tic tac tic tac
echo ======================================================
echo.
echo ======================================================
echo 1. exit 
echo 2. refresh the clock 
echo    Or enter to refresh
echo ======================================================
for /f "tokens=1-3 delims=:." %%a in ("%time%") do (
echo                       %%a:%%b:%%c
)
echo ======================================================
timeout /t 1 >nul

set	/p choice=Enter your choice: 
if  "%choice%"=="1" goto system 
if  "%choice%"=="2" goto Clock
goto clock


:passmanager
cls
echo ======================================================
echo                 PASSWORD MANAGER
echo ======================================================
set "pass_dir=%~dp0G\pass"
set "pass_file=%pass_dir%\password.txt"


if not exist "%pass_dir%" mkdir "%pass_dir%"


if not exist "%pass_file%" (
    echo Password file not found, creating a default one...
    echo [admin]=[adminpassword123] > "%pass_file%"  
)

echo 1. Add New User Password
echo 2. View All User Passwords
echo 3. Delete user
echo 4. Back to System Menu
set /p passchoice=Enter your choice: 

if "%passchoice%"=="1" goto add_password
if "%passchoice%"=="2" goto view_password
if "%passchoice%"=="3" goto delete_user
if "%passchoice%"=="4" goto system
goto passmanager


:add_password
cls
echo ======================================================
echo                  ADD NEW USER PASSWORD
echo ======================================================
set /p username=Enter new username: 
set /p password=Enter new password: 


call :sanitize_input

findstr /i "^[%username%]=[%password%]" "%pass_file%" >nul
if %errorlevel%==0 (
    echo Error: User %username% already exists!
    timeout /t 2 >nul
    goto passmanager
)

echo [%username%]=[%password%] >> "%pass_file%"
echo New user %username% added successfully!
timeout /t 2 >nul
goto passmanager

:sanitize_input

set "username=%username:&=_amp%;^=^&%"
set "password=%password:&=_amp%;^=^&%"
goto :eof


:delete_user
cls
echo ======================================================
echo             DELETE USER FROM PASSWORD FILE
echo ======================================================
set /p dev_password=Enter DEV password to delete user: 
if "%dev_password%"=="10122009" (
    set /p username=Enter the username to delete: 


    call :sanitize_input

    set "pass_file=%~dp0G\pass\password.txt"
    
  
    findstr /v /c:"[%username%]=" "%pass_file%" > "%pass_file%.tmp"


    if exist "%pass_file%.tmp" (
        move /y "%pass_file%.tmp" "%pass_file%"
        echo User "[%username%]" deleted successfully!
    ) else (
        echo User "[%username%]" not found!
    )
) else (
    echo Incorrect DEV password!
)
pause
goto passmanager

:sanitize_input

set "username=%username:&=_amp%;^=^&%"
goto :eof


:sanitize_input

set "username=%username:&=_amp%;^=^&%"
goto :eof


:view_password
cls
echo ======================================================
echo                  VIEW SAVED PASSWORDS
echo ======================================================
set /p dev_password=Enter DEV password to view passwords: 
if "%dev_password%"=="10122009" (
    set "pass_dir=%~dp0G\pass"
    set "pass_file=%pass_dir%\password.txt"

    
    if exist "%pass_file%" (
        type "%pass_file%" 
    ) else (
        echo Error: The password file does not exist!
        echo Do you want to create a new password file? (y/n)
        set /p create_new_file=Enter choice: 
        if /i "%create_new_file%"=="y" (
            echo [admin]=[adminpassword123] > "%pass_file%"
            echo New password file created with default admin credentials!
        ) else (
            echo Returning to password manager menu...
        )
    )
) else (
    echo Incorrect DEV password!
)
pause
goto passmanager


:sysimformation
color 0f
cls
echo ======================================================
echo                SYSTEM INFORMATION
echo ======================================================
echo Computer Name: %COMPUTERNAME%
echo Username: %USERNAME%
echo Operating System: DOS
echo Processor: 
wmic cpu get Name | findstr /v "Name"
echo RAM Size: 512 MB
echo Available Disk Space: 10GB
echo ======================================================
pause
goto system


:setting
color 1f
cls
echo ======================================================
echo                   SYSTEM SETTINGS
echo ======================================================
echo.
echo 1. RAM setting
echo 2. Disk setting
echo 3. exit

set /p sttchoice=Enter your choice here:

if "%sttchoice%"=="1" goto ramsetting
if "%sttchoice%"=="2" goto disksetting
if "%sttchoice%"=="3" goto bootmenu


:ramsetting
color f0
cls
echo ======================================================
echo                      RAM SETTING
echo         you can change 8.388.608 bit a time 
echo ======================================================
echo.
echo Memory 512MB
echo Boot by DOS 
echo Error not found
pause
goto setting


:devtoolc
cls
color 1F
echo ======================================================
echo                   DEV SAFE SCREEN
echo ======================================================
echo.

set /p dev_password=Enter DEV password: 

if "%dev_password%"=="10122009" (
    echo Access granted!
    goto devmode
) else (
    echo Incorrect password!
)
goto devtoolc
pause


:devmode
color 0A
cls
echo ======================================================
echo                  WELCOME TO DEV TOOL
echo ======================================================
echo 1. system file manager
echo 2. Delete the system 
echo 3. reset the system
echo 4. exit 
echo ======================================================
set /p devchoice=enter your choice: 

if "%devchoice%"=="1" goto devfile
if "%devchoice%"=="2" goto devdelete
if "%devchoice%"=="3" goto resetsys
if "%devchoice%"=="4" goto bootmenu


:devfile
set "root=%~dp0G"
if not exist "%root%" mkdir "%root%"
cd /d "%root%"
cls
echo ======================================================
echo                   DEV FILE MANAGER 
echo                careful with the system
echo ======================================================
echo 1. Create Folder
echo 2. Create File
echo 3. Delete File/Folder
echo 4. Open File
echo 5. Change Directory
echo 6. Go to G:
echo 7. see local disk and file 
echo 8. Exit
echo ======================================================
set /p choice=Enter your choice: 

if "%choice%"=="1" goto create_folderdev
if "%choice%"=="2" goto create_filedev
if "%choice%"=="3" goto deletedev
if "%choice%"=="4" goto open_filedev
if "%choice%"=="5" goto change_dirdev
if "%choice%"=="6" cd /d "%root%" && goto devfile
if "%choice%"=="7" goto fileseedev
if "%choice%"=="8" goto systemdev
goto devfile

:create_folderdev
set /p foldername=Enter folder name: 
mkdir "%foldername%" && echo Folder "%foldername%" created!
pause
goto devfile

:create_filedev
set /p filename=Enter file name: 
type nul > "%filename%" && echo File "%filename%" created!
pause
goto devfile

:deletedev
set /p target=Enter file/folder to delete: 
if exist "%target%" (rmdir /s /q "%target%" 2>nul || del /f /q "%target%") && echo "%target%" deleted!
pause
goto devfile

:open_filedev
set /p filename=Enter file name: 
if exist "%filename%" (more "%filename%" 2>nul || start "" "%filename%") else echo File not found!
pause
goto devfile

:change_dirdev
set /p foldername=Enter folder name: 
if exist "%foldername%" cd /d "%cd%\%foldername%" && echo Entered "%foldername%"!
pause
goto devfile

:fileseedev
cls
echo ======================================================
echo                  LIST OF FILES & FOLDERS               
echo ======================================================
echo.
echo [Folders:]
for /d %%D in (*) do echo %%D
echo.
echo [Files:]
for %%i in (*) do if not "%%i"=="desktop.ini" echo %%i
echo ======================================================
pause
goto devfile


:devdelete
color 47
echo ======================================================
echo                     ARE YOU SURE
echo ======================================================
set /p devD=enter your choice(Y/N):

if "%devD%"=="Y" goto yes
if "%devD%"=="N" goto no 


:yes
echo goodbye
timeout /t 1 /nobreak >nul
goto next


:next
echo Goodbye
timeout /t 1 /nobreak >nul
echo Error: System file not found!
ping -n 2 127.0.0.1 >nul
echo |                           |
ping -n 2 127.0.0.1 >nul
goto next


:no
echo thank you for choosing
pause
goto bootmenu


:resetsys
cls
echo you must restart to reset 
timeout /t 1 >nul
pause
color
cls
echo ======================================================
echo                  SYSTEM RESTARTING
echo ======================================================
echo The system will restart in 5 seconds...
timeout /t 5 >nul
goto reafter


:reafter
cls 
echo you are reset :)
timeout /t 1 >nul
goto bootmenu


:disksetting
color f0
cls
echo ======================================================
echo                      DISK SETTING
echo           you can change 12.092.211 bit a time 
echo ======================================================
echo.
echo disk size: 10GB 
echo free space: 9,4GB
echo I'm Disk, I'm wanna tell you, don't change anything 
echo because that's your memories
echo bye
pause 
goto setting


:restart
cls
echo ======================================================
echo                  SYSTEM RESTARTING
echo ======================================================
echo The system will restart in 5 seconds...
timeout /t 5 >nul

goto :bootmenu


:exit
color 0f
cls 
echo ======================================================
echo                    EXIT THE SYSTEM
echo                      see you soon
echo                     support by cmd
echo ======================================================
pause
exit