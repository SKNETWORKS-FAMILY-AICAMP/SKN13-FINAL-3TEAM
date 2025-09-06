import sys, json, base64
from pathlib import Path
from PIL import Image
import io

# handler를 직접 import하여 rp_handler를 호출
import handler as H

def to_data_uri(img_path: str) -> str:
    p = Path(img_path)
    if not p.exists():
        raise FileNotFoundError(img_path)
    mime = "image/png" if p.suffix.lower()==".png" else "image/jpeg"
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python local_invoke.py /workspace/payload_3d.json [seed_image_path]")
        sys.exit(1)

    payload_path = Path(sys.argv[1])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    # seed 이미지를 두 번째 인자로 넘기거나, 기본 시드 이미지를 생성해 삽입
    if len(sys.argv) >= 3:
        seed_img = sys.argv[2]
        payload["input"]["image"] = to_data_uri(seed_img)
    else:
        # 256x256 단색 시드 이미지 생성(테스트용)
        img = Image.new("RGB", (256, 256), (200, 200, 200))
        buf = io.BytesIO(); img.save(buf, "PNG")
        payload["input"]["image"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    # handler 호출
    result = H.rp_handler({"input": payload.get("input", {})})
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
