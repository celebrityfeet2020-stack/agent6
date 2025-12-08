#!/bin/bash
set -e

MODE=${1:-sing-box}

echo "========================================="
echo "  透明网关容器启动"
echo "========================================="
echo "模式: $MODE"
echo "容器IP: $(hostname -I)"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 显示版本信息
echo "已安装组件:"
echo "  - sing-box: $(sing-box version 2>&1 | head -1)"
echo "  - Mihomo: $(mihomo -v 2>&1 | head -1)"
echo "  - WireGuard: $(wg version 2>&1)"
echo "  - iptables: $(iptables --version 2>&1 | head -1)"
echo "  - nftables: $(nft --version 2>&1)"
echo ""

# 启用IP转发
echo "1" > /proc/sys/net/ipv4/ip_forward
echo "1" > /proc/sys/net/ipv6/conf/all/forwarding 2>/dev/null || true
echo "✓ IP转发已启用"

# 加载内核模块（如果需要）
modprobe xt_TPROXY 2>/dev/null || echo "⚠ TPROXY模块加载失败（可能已内置）"
modprobe xt_socket 2>/dev/null || echo "⚠ socket模块加载失败（可能已内置）"
modprobe xt_mark 2>/dev/null || echo "⚠ mark模块加载失败（可能已内置）"

echo ""

# 根据模式启动不同服务
case "$MODE" in
    sing-box)
        echo "========================================="
        echo "  启动 sing-box 模式"
        echo "========================================="
        
        if [ ! -f /etc/sing-box/config.json ]; then
            echo "✗ 错误: 配置文件不存在 /etc/sing-box/config.json"
            exit 1
        fi
        
        echo "验证配置文件..."
        if ! sing-box check -c /etc/sing-box/config.json; then
            echo "✗ 错误: 配置文件验证失败"
            exit 1
        fi
        
        echo "✓ 配置验证通过"
        echo ""
        exec sing-box run -c /etc/sing-box/config.json
        ;;
        
    mihomo)
        echo "========================================="
        echo "  启动 Mihomo 模式"
        echo "========================================="
        
        if [ ! -f /etc/mihomo/config.yaml ]; then
            echo "✗ 错误: 配置文件不存在 /etc/mihomo/config.yaml"
            exit 1
        fi
        
        echo "✓ 配置文件存在"
        echo ""
        exec mihomo -d /etc/mihomo -f /etc/mihomo/config.yaml
        ;;
        
    wireguard)
        echo "========================================="
        echo "  启动 WireGuard 模式"
        echo "========================================="
        
        if [ ! -f /etc/wireguard/wg0.conf ]; then
            echo "✗ 错误: 配置文件不存在 /etc/wireguard/wg0.conf"
            exit 1
        fi
        
        echo "启动 WireGuard 接口..."
        wg-quick up wg0
        echo "✓ WireGuard 已启动"
        echo ""
        
        # 保持容器运行
        tail -f /dev/null
        ;;
        
    *)
        echo "✗ 错误: 未知模式 '$MODE'"
        echo "支持的模式: sing-box, mihomo, wireguard"
        exit 1
        ;;
esac
