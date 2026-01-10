#!/bin/bash

# PNG转ICO脚本
# 使用方法: ./png2ico.sh input.png [output.ico]

INPUT="$1"
OUTPUT="${2:-${INPUT%.*}.ico}"

if [ -z "$INPUT" ]; then
    echo "使用方法: $0 <输入文件> [输出文件]"
    echo "示例: $0 icon.png favicon.ico"
    exit 1
fi

if ! command -v convert &> /dev/null; then
    echo "正在安装ImageMagick..."
    brew install imagemagick
fi

echo "正在转换 $INPUT 为 $OUTPUT ..."

# 创建临时目录
TEMP_DIR=$(mktemp -d)

# 生成不同尺寸
sizes=(16 32 48 64 128 256 512 1024)
for size in "${sizes[@]}"; do
    convert "$INPUT" -resize ${size}x${size} "${TEMP_DIR}/icon_${size}.png"
done

# 合并为ICO
convert "${TEMP_DIR}"/icon_*.png -define icon:auto-resize "${OUTPUT}"

# 清理
rm -rf "$TEMP_DIR"

echo "✅ 转换完成: $OUTPUT"