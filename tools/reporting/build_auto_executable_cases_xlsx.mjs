import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..", "..");
const statusPath = path.join(rootDir, "config", "polaris_doc_case_status.json");

function buildStamp() {
  const now = new Date();
  const pad = (v) => String(v).padStart(2, "0");
  return [
    now.getFullYear(),
    pad(now.getMonth() + 1),
    pad(now.getDate()),
    pad(now.getHours()),
    pad(now.getMinutes()),
    pad(now.getSeconds()),
  ].join("");
}

function numericCaseOrder(caseId) {
  const parts = String(caseId || "").split("_");
  const tail = parts[parts.length - 1] || "";
  const num = Number.parseInt(tail, 10);
  return Number.isFinite(num) ? num : Number.MAX_SAFE_INTEGER;
}

function sortCases(rows) {
  return [...rows].sort((a, b) => {
    const diff = numericCaseOrder(a.case_id) - numericCaseOrder(b.case_id);
    if (diff !== 0) {
      return diff;
    }
    return String(a.case_id || "").localeCompare(String(b.case_id || ""), "zh-CN");
  });
}

function rowMatrix(rows) {
  return rows.map((item, index) => [
    index + 1,
    item.case_id || "",
    item.name || "",
    item.mode || "",
    item.priority || "",
    item.runner_kind || "",
    item.result || "",
    item.reason || "",
  ]);
}

async function saveBlob(blob, savePath) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  await fs.writeFile(savePath, bytes);
}

async function main() {
  const stamp = buildStamp();
  const outputDir = path.join(rootDir, "outputs", "auto_cases", `${stamp}_polaris_auto_cases`);
  await fs.mkdir(outputDir, { recursive: true });

  const status = JSON.parse(await fs.readFile(statusPath, "utf8"));
  const effective = status.effective_counts_after_recheck || {};
  const env = status.environment || {};
  const cases = sortCases(
    (status.cases || []).filter((item) => item.classification === "auto_executable_now"),
  );

  const workbook = Workbook.create();
  const summarySheet = workbook.worksheets.add("摘要");
  const caseSheet = workbook.worksheets.add("可测试用例");

  summarySheet.showGridLines = false;
  caseSheet.showGridLines = false;
  summarySheet.freezePanes.freezeRows(1);
  caseSheet.freezePanes.freezeRows(1);

  summarySheet.getRange("A1:F1").merge();
  summarySheet.getRange("A1").values = [["Polaris 当前可测试用例清单"]];
  summarySheet.getRange("A1").format = {
    fill: "#0F4C5C",
    font: { bold: true, color: "#FFFFFF", size: 16 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };
  summarySheet.getRange("A1:F1").format.rowHeightPx = 30;

  summarySheet.getRange("A3:B14").values = [
    ["生成时间", status.updated_at || ""],
    ["执行阶段", "debug"],
    ["稳定性用例", "已剔除，待全链路走通后恢复"],
    ["活跃结果会话", status.session_dir || ""],
    ["当前环境", env.env_label || ""],
    ["当前 Wi-Fi", env.connected_ssid || ""],
    ["可测试用例数", effective.auto_executable_now || cases.length],
    ["已执行", effective.executed || 0],
    ["PASS", effective.pass || 0],
    ["FAIL", effective.fail || 0],
    ["BLOCKED", effective.blocked || 0],
    ["说明", "本表仅保留当前调试阶段可自动执行的用例"],
  ];
  summarySheet.getRange("A3:A14").format = {
    fill: "#DCEEF2",
    font: { bold: true, color: "#12343B" },
  };
  summarySheet.getRange("A3:B14").format.wrapText = true;
  summarySheet.getRange("A3:B14").format.rowHeightPx = 24;
  summarySheet.getRange("A3:A14").format.columnWidthPx = 150;
  summarySheet.getRange("B3:B14").format.columnWidthPx = 520;

  const headers = [["序号", "用例ID", "用例名称", "模式", "优先级", "runner_kind", "当前结果", "自动化说明"]];
  caseSheet.getRange("A1:H1").values = headers;
  caseSheet.getRange(`A2:H${cases.length + 1}`).values = rowMatrix(cases);

  caseSheet.getRange("A1:H1").format = {
    fill: "#0F4C5C",
    font: { bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };
  caseSheet.getRange(`A1:H${cases.length + 1}`).format.wrapText = true;
  caseSheet.getRange(`A2:A${cases.length + 1}`).format.horizontalAlignment = "center";
  caseSheet.getRange(`D2:G${cases.length + 1}`).format.horizontalAlignment = "center";
  caseSheet.getRange("A:A").format.columnWidthPx = 58;
  caseSheet.getRange("B:B").format.columnWidthPx = 110;
  caseSheet.getRange("C:C").format.columnWidthPx = 300;
  caseSheet.getRange("D:D").format.columnWidthPx = 90;
  caseSheet.getRange("E:E").format.columnWidthPx = 80;
  caseSheet.getRange("F:F").format.columnWidthPx = 170;
  caseSheet.getRange("G:G").format.columnWidthPx = 90;
  caseSheet.getRange("H:H").format.columnWidthPx = 500;

  caseSheet.getRange(`G2:G${cases.length + 1}`).conditionalFormats.addCustom(
    '=G2="PASS"',
    { fill: "#DCFCE7", font: { color: "#166534", bold: true } },
  );
  caseSheet.getRange(`G2:G${cases.length + 1}`).conditionalFormats.addCustom(
    '=G2="FAIL"',
    { fill: "#FEE2E2", font: { color: "#991B1B", bold: true } },
  );
  caseSheet.getRange(`G2:G${cases.length + 1}`).conditionalFormats.addCustom(
    '=G2="BLOCKED"',
    { fill: "#FEF3C7", font: { color: "#92400E", bold: true } },
  );

  caseSheet.tables.add(`A1:H${cases.length + 1}`, true, "PolarisAutoExecutableCases");

  const summaryInspect = await workbook.inspect({
    kind: "table",
    range: "摘要!A1:B14",
    include: "values",
    tableMaxRows: 20,
    tableMaxCols: 4,
  });
  const casesInspect = await workbook.inspect({
    kind: "table",
    range: `可测试用例!A1:H12`,
    include: "values",
    tableMaxRows: 12,
    tableMaxCols: 8,
  });

  await fs.writeFile(path.join(outputDir, "inspect_summary.ndjson"), summaryInspect.ndjson, "utf8");
  await fs.writeFile(path.join(outputDir, "inspect_cases.ndjson"), casesInspect.ndjson, "utf8");

  const summaryPreview = await workbook.render({
    sheetName: "摘要",
    range: "A1:B14",
    scale: 1,
    format: "png",
  });
  const casesPreview = await workbook.render({
    sheetName: "可测试用例",
    range: "A1:H18",
    scale: 1,
    format: "png",
  });
  await saveBlob(summaryPreview, path.join(outputDir, "summary_preview.png"));
  await saveBlob(casesPreview, path.join(outputDir, "cases_preview.png"));

  const xlsx = await SpreadsheetFile.exportXlsx(workbook);
  const xlsxPath = path.join(outputDir, "polaris_auto_executable_cases.xlsx");
  await xlsx.save(xlsxPath);

  const meta = {
    exported_at: new Date().toISOString(),
    xlsx_path: xlsxPath,
    output_dir: outputDir,
    row_count: cases.length,
    counts: {
      auto_executable_now: effective.auto_executable_now || cases.length,
      executed: effective.executed || 0,
      pass: effective.pass || 0,
      fail: effective.fail || 0,
      blocked: effective.blocked || 0,
      skip: effective.skip || 0,
    },
  };
  await fs.writeFile(
    path.join(outputDir, "export_meta.json"),
    JSON.stringify(meta, null, 2),
    "utf8",
  );

  console.log(JSON.stringify(meta, null, 2));
}

await main();
