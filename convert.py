from pathlib import Path
import json
input_path = Path(r"C:\Users\Admin\Downloads\DATADetect\raid_mistral_test.json")
output_path = Path(r"C:\Users\Admin\Downloads\DATADetect\raid_mistral_test_repre.json")

human_texts = []
machine_texts = []

with input_path.open("r", encoding="utf-8") as f:
    for line_no, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue

        item = json.loads(line)
        text = item.get("text", "").strip()
        label = str(item.get("label", "")).strip().lower()

        if not text:
            continue

        if label == "human":
            human_texts.append(text)
        elif label in ("machine", "ai", "generated"):
            machine_texts.append(text)
        else:
            print(f"Bo qua dong {line_no}: label={label!r}")

if len(human_texts) != len(machine_texts):
    raise ValueError(
        f"So luong khong bang nhau: human={len(human_texts)}, "
        f"machine={len(machine_texts)}. Can kiem tra dataset."
    )

records = []
for i, (human, machine) in enumerate(
    zip(human_texts, machine_texts), 1
):
    records.append({
        "id": f"raid_{i:05d}",
        "domain": "raid",
        "llm_type": "llama_greedy",
        "human_text": human,
        "direct_prompt": machine
    })

output_path.parent.mkdir(parents=True, exist_ok=True)
with output_path.open("w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"Human: {len(human_texts)}")
print(f"Machine: {len(machine_texts)}")
print(f"Pairs: {len(records)}")
print(f"Saved: {output_path}")
