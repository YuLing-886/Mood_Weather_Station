const suffixes = [
  "维吾尔自治区",
  "壮族自治区",
  "回族自治区",
  "自治区",
  "特别行政区",
  "省",
  "市"
];

export function normalizeProvinceName(name: string) {
  let value = String(name ?? "").trim();
  for (const suffix of suffixes) {
    if (value.endsWith(suffix)) {
      value = value.slice(0, -suffix.length);
    }
  }
  if (value === "内蒙古自治区") return "内蒙古";
  if (value === "宁夏回族") return "宁夏";
  if (value === "广西壮族") return "广西";
  if (value === "新疆维吾尔") return "新疆";
  return value;
}
