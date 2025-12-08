# sing-box透明网关Docker镜像

## 镜像信息

- **Docker Hub**: `junpeng999/singbox-gateway:latest`
- **架构**: AMD64
- **基础镜像**: Alpine Linux 3.19

## 包含组件

| 组件 | 版本 | 用途 |
|------|------|------|
| sing-box | 1.10.6 | 主要代理工具（TUN模式） |
| Mihomo | 1.18.10 | 备选代理工具（TPROXY/REDIRECT） |
| WireGuard | latest | VPN隧道 |
| iptables | latest | 防火墙规则 |
| nftables | latest | 新一代防火墙 |
| iproute2 | latest | 路由管理 |
| ipset | latest | IP集合管理 |
| tcpdump | latest | 网络抓包调试 |

## 快速开始

### 1. 拉取镜像

```bash
docker pull junpeng999/singbox-gateway:latest
```

### 2. 准备配置文件

在D5上创建配置目录：

```bash
mkdir -p /home/double5090/singbox-gateway/{config,data}
```

将sing-box配置文件放到 `config/config.json`

### 3. 创建Macvlan网络

```bash
docker network create -d macvlan \
  --subnet=192.168.9.0/24 \
  --gateway=192.168.9.1 \
  -o parent=enp7s0 \
  vpn_macvlan_enp7s0
```

### 4. 启动容器

```bash
docker run -d \
  --name singbox-gateway \
  --network vpn_macvlan_enp7s0 \
  --ip 192.168.9.201 \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  --sysctl net.ipv4.ip_forward=1 \
  --sysctl net.ipv6.conf.all.forwarding=1 \
  -v /home/double5090/singbox-gateway/config:/etc/sing-box \
  -v /home/double5090/singbox-gateway/data:/var/lib/sing-box \
  --restart unless-stopped \
  junpeng999/singbox-gateway:latest
```

## 运行模式

容器支持三种运行模式：

### sing-box模式（默认）

```bash
docker run ... junpeng999/singbox-gateway:latest sing-box
```

### Mihomo模式

```bash
docker run ... \
  -v /path/to/mihomo/config:/etc/mihomo \
  junpeng999/singbox-gateway:latest mihomo
```

### WireGuard模式

```bash
docker run ... \
  -v /path/to/wireguard/config:/etc/wireguard \
  junpeng999/singbox-gateway:latest wireguard
```

## 客户端配置

### Mac/Linux

```bash
# 设置网关
sudo route add default 192.168.9.201

# 设置DNS
sudo networksetup -setdnsservers Wi-Fi 114.114.114.114
```

### Windows

```powershell
# 在网络设置中修改
# 网关: 192.168.9.201
# DNS: 114.114.114.114
```

## 调试命令

```bash
# 进入容器
docker exec -it singbox-gateway sh

# 查看日志
docker logs -f singbox-gateway

# 查看路由
docker exec singbox-gateway ip route

# 查看iptables
docker exec singbox-gateway iptables -L -n -v

# 测试DNS
docker exec singbox-gateway nslookup google.com

# 抓包调试
docker exec singbox-gateway tcpdump -i any port 53
```

## 故障排查

### 1. 容器无法启动

检查配置文件是否存在：
```bash
ls -la /home/double5090/singbox-gateway/config/
```

### 2. DNS解析失败

检查53端口是否监听：
```bash
docker exec singbox-gateway netstat -tunlp | grep 53
```

### 3. 无法访问外网

检查WireGuard连接：
```bash
docker exec singbox-gateway sing-box version
docker logs singbox-gateway | grep wireguard
```

## 性能优化

### MTU调整

在配置文件中调整WireGuard MTU：

```json
{
  "outbounds": [{
    "type": "wireguard",
    "mtu": 1420
  }]
}
```

### TCP BBR

容器已启用，无需额外配置。

## 更新镜像

```bash
# 停止容器
docker stop singbox-gateway

# 删除容器
docker rm singbox-gateway

# 拉取最新镜像
docker pull junpeng999/singbox-gateway:latest

# 重新启动（使用上面的启动命令）
```

## 技术支持

- GitHub Issues: https://github.com/celebrityfeet2020-stack/agent6/issues
- Docker Hub: https://hub.docker.com/r/junpeng999/singbox-gateway
