# Cambia estas rutas y datos con tus propios valores
$VPSUser = "ubuntu"
$VPSHost = "3.19.56.195"
$PEMPath = "C:\Users\Kunzeu\Downloads\Qalizs.pem"
$RemotePath = "~/QalizPy"
$ContainerName = "qaliz-bot-container"

# Comandos remotos
$RemoteCommand = @"
cd $RemotePath
git pull origin main
docker build -t qaliz-bot .
docker stop $ContainerName || true
docker rm $ContainerName || true
docker run -d --restart always --name $ContainerName qaliz-bot
"@

# Ejecuta el SSH con los comandos
ssh -i $PEMPath "$VPSUser@$VPSHost" "$RemoteCommand"
