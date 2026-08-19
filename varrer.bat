@echo off
REM ============================================================
REM  CFC ACADEMY - RADAR CONCURSOS CONTABILIDADE
REM  Varredura das bancas + publicacao no site.
REM ------------------------------------------------------------
REM  Roda na MAQUINA do Patrick, agendado pelo Windows.
REM  Substitui o GitHub Actions, que ficava falhando.
REM
REM  Para agendar (uma vez so, no PowerShell como admin):
REM    schtasks /create /tn "Radar Concursos Contabilidade" /tr "CAMINHO\varrer.bat" ^
REM             /sc daily /st 07:00
REM
REM  Para rodar agora, so dar duplo clique.
REM ============================================================

cd /d "%~dp0"

echo.
echo === Radar Concursos Contabilidade - varredura de %date% %time%
echo.

python robo\atualizar.py --limite 60
if errorlevel 1 (
    echo.
    echo FALHOU a varredura. Nada foi publicado.
    pause
    exit /b 1
)

REM So publica se o arquivo mudou de fato.
git diff --quiet -- data/editais.json data/organizadoras.json
if errorlevel 1 (
    echo.
    echo Mudancas encontradas. Publicando...
    git add data/editais.json data/organizadoras.json
    git commit -m "chore(radar): varredura automatica de %date%"
    git push
    echo Publicado. O site atualiza em cerca de 1 minuto.
) else (
    echo.
    echo Nenhum edital novo hoje. Site intacto.
)

echo.
pause
