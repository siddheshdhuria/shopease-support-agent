#!/bin/bash
# EC2 (Amazon Linux 2023) pe EK BAAR chalao:  bash ec2-setup.sh
set -e

echo "📦 Installing Docker..."
sudo dnf update -y
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user

echo "🔑 Creating env file (OpenAI key sirf server pe rahegi, GitHub/pipeline me nahi)..."
if [ ! -f /home/ec2-user/shopease.env ]; then
  read -r -s -p "Enter OPENAI_API_KEY: " KEY; echo
  cat > /home/ec2-user/shopease.env << ENVEOF
OPENAI_API_KEY=$KEY
CHAT_MODEL=gpt-4o-mini
EMBED_MODEL=text-embedding-3-small
ENVEOF
  chmod 600 /home/ec2-user/shopease.env
fi

aws --version
echo "✅ Setup done. Ek baar logout karke dobara SSH karo (docker group apply hone ke liye)."
