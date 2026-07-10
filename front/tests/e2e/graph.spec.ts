import { expect, test } from "@playwright/test";

// グラフ画面が slice API（design §10.4）から取得したノード・エッジを描画できることを検証する。
// データ源は BigQuery / seed フォールバックのどちらでもよい（どちらも edges を返す）。
test("graph page renders nodes and edges from the slice API", async ({ page }) => {
  await page.goto("/graph");

  await expect(page.getByRole("heading", { name: "Knowledge Graph" })).toBeVisible();
  // meta.source の可視化（BigQuery 実データ / サンプルデータ）
  await expect(page.getByText(/BigQuery 実データ|サンプルデータ/)).toBeVisible();

  // ノードとエッジ（SVG line）が描画されること — 旧 /graph/nodes の BQ 経路では
  // edges が返らず線が消える退行があったため、ここで担保する
  await expect(page.locator("svg line").first()).toBeVisible();
  await expect(page.getByText(/Nodes \d+ \/ Relations [1-9]\d*/)).toBeVisible();

  // 仮説エッジの凡例（Fact / Hypothesis の区別、R6）
  await expect(page.getByText("Hypothesis graph")).toBeVisible();
});
