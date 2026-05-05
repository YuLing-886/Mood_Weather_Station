/**
 * Date formatting utilities for converting ISO week strings to human-readable date ranges.
 * Input format: "2020-W05" (ISO week numbering)
 */

/** Parse "2020-W05" to the Monday date of that ISO week */
function isoWeekToDate(isoWeek: string): Date {
  const match = isoWeek.match(/^(\d{4})-W(\d{2})$/);
  if (!match) return new Date();
  const year = parseInt(match[1], 10);
  const week = parseInt(match[2], 10);

  // Jan 4 is always in ISO week 1
  const jan4 = new Date(year, 0, 4);
  // Find Monday of week 1
  const dayOfWeek = jan4.getDay() || 7; // Sunday = 7
  const week1Monday = new Date(jan4);
  week1Monday.setDate(jan4.getDate() - dayOfWeek + 1);

  // Target Monday
  const target = new Date(week1Monday);
  target.setDate(week1Monday.getDate() + (week - 1) * 7);
  return target;
}

/** Format a date as "M月D日" */
function formatChineseShort(d: Date): string {
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}

/** Format a date as "YYYY年M月D日" */
function formatChineseFull(d: Date): string {
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
}

/** Format a date as "MM.DD" */
function formatDot(d: Date): string {
  return `${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

/** Full range: "2020年3月1日-3月7日" */
export function dateWeekToFullRange(isoWeek: string): string {
  const start = isoWeekToDate(isoWeek);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);

  if (start.getFullYear() === end.getFullYear()) {
    return `${formatChineseFull(start)}-${end.getMonth() + 1}月${end.getDate()}日`;
  }
  return `${formatChineseFull(start)}-${formatChineseFull(end)}`;
}

/** Short range: same year → "3月1日-3月7日"; cross year → "2019年12月30日-2020年1月5日" */
export function dateWeekToShortRange(isoWeek: string): string {
  const start = isoWeekToDate(isoWeek);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);

  if (start.getFullYear() !== end.getFullYear()) {
    return `${formatChineseFull(start)}-${formatChineseFull(end)}`;
  }
  if (start.getMonth() === end.getMonth()) {
    return `${formatChineseShort(start)}-${end.getDate()}日`;
  }
  return `${formatChineseShort(start)}-${formatChineseShort(end)}`;
}

/** Axis range: "03.01-03.07" */
export function dateWeekToAxisRange(isoWeek: string): string {
  const start = isoWeekToDate(isoWeek);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  return `${formatDot(start)}-${formatDot(end)}`;
}

/** Month string "2020-01" to "2020年1月" */
export function dateMonthToChinese(dateMonth: string): string {
  const match = dateMonth.match(/^(\d{4})-(\d{2})$/);
  if (!match) return dateMonth;
  return `${match[1]}年${parseInt(match[2], 10)}月`;
}

/** Short month: "2020-01" to "1月" */
export function dateMonthToShort(dateMonth: string): string {
  const match = dateMonth.match(/^\d{4}-(\d{2})$/);
  if (!match) return dateMonth;
  return `${parseInt(match[1], 10)}月`;
}
