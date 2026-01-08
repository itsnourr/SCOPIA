@echo off
REM Helper script to run Maven with Java 23
REM This script sets JAVA_HOME to Java 23 before running Maven
REM
REM Usage: mvn-java23.bat <maven-command>
REM Example: mvn-java23.bat clean install
REM Example: mvn-java23.bat spring-boot:run

REM Common Java 23 installation paths
set JAVA23_HOME=

REM Check common installation locations
if exist "C:\Program Files\Java\jdk-23" (
    set JAVA23_HOME=C:\Program Files\Java\jdk-23
) else if exist "C:\Program Files\Java\jdk23" (
    set JAVA23_HOME=C:\Program Files\Java\jdk23
) else if exist "C:\Program Files\Eclipse Adoptium\jdk-23" (
    set JAVA23_HOME=C:\Program Files\Eclipse Adoptium\jdk-23
) else if exist "C:\Program Files\Microsoft\jdk-23" (
    set JAVA23_HOME=C:\Program Files\Microsoft\jdk-23
) else if exist "C:\Program Files\Java\jdk-23.0.1" (
    set JAVA23_HOME=C:\Program Files\Java\jdk-23.0.1
) else if exist "C:\Program Files\Java\jdk-23.0.2" (
    set JAVA23_HOME=C:\Program Files\Java\jdk-23.0.2
)

if "%JAVA23_HOME%"=="" (
    echo.
    echo ERROR: Java 23 not found in standard locations!
    echo.
    echo Please update this script with the correct path to your Java 23 installation.
    echo Or set JAVA23_HOME manually before running this script.
    echo.
    echo Example: set JAVA23_HOME=C:\Program Files\Java\jdk-23
    echo.
    exit /b 1
)

echo Using Java 23 from: %JAVA23_HOME%
set JAVA_HOME=%JAVA23_HOME%
set PATH=%JAVA23_HOME%\bin;%PATH%

REM Verify Java version
java -version
echo.

mvn %*
