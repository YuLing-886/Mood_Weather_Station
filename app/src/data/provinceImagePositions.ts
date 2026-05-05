/**
 * Province bubble positions on china_map.jpg as percentage coordinates.
 * x = left%, y = top%  (0-100 relative to the image).
 * Dense clusters include label offsets to reduce overlap.
 */

export interface ProvinceImagePos {
  x: number;
  y: number;
  /** Optional pixel offset for the text label (dx, dy) */
  labelOffset?: [number, number];
}

export const PROVINCE_IMAGE_POSITIONS: Record<string, ProvinceImagePos> = {
  新疆:   { x: 22.9, y: 35.5 },
  西藏:   { x: 25.0, y: 63.0 },
  青海:   { x: 35.0, y: 54.0 },
  甘肃:   { x: 35.4, y: 51.7 },
  宁夏:   { x: 49.6, y: 48.5 },
  内蒙古: { x: 56.5, y: 36.4 },
  北京:   { x: 62.4, y: 39.3, labelOffset: [14, -6] },
  天津:   { x: 64.0, y: 41.5, labelOffset: [14, 4] },
  河北:   { x: 61.8, y: 44.9, labelOffset: [-16, 8] },
  山西:   { x: 57.6, y: 48.4 },
  黑龙江: { x: 75.7, y: 19.1 },
  吉林:   { x: 74.2, y: 27.5 },
  辽宁:   { x: 71.0, y: 34.6 },
  山东:   { x: 66.0, y: 49.7 },
  江苏:   { x: 69.7, y: 58.3, labelOffset: [14, -6] },
  上海:   { x: 72.1, y: 62.3, labelOffset: [14, 0] },
  安徽:   { x: 65.9, y: 62.0 },
  浙江:   { x: 70.6, y: 67.8, labelOffset: [14, 4] },
  福建:   { x: 67.8, y: 76.8 },
  江西:   { x: 63.5, y: 73.2 },
  河南:   { x: 60.1, y: 56.7 },
  湖北:   { x: 59.0, y: 65.1 },
  湖南:   { x: 58.4, y: 74.2 },
  广东:   { x: 62.5, y: 84.4 },
  广西:   { x: 54.1, y: 84.4 },
  海南:   { x: 55.8, y: 96.3 },
  四川:   { x: 44.0, y: 67.0 },
  重庆:   { x: 51.3, y: 68.6 },
  贵州:   { x: 52.7, y: 76.8 },
  云南:   { x: 42.0, y: 82.0 },
  陕西:   { x: 52.6, y: 58.1 },
  台湾:   { x: 73.4, y: 80.7 },
  香港:   { x: 56.3, y: 92.5, labelOffset: [12, 0] },
  澳门:   { x: 55.0, y: 83.0, labelOffset: [-14, 0] },
};
