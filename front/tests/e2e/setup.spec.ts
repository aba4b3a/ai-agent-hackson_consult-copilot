import { expect, test } from "@playwright/test";

test("consultant can open the workspace setup screen", async ({ page }) => {
  await page.goto("/setup");

  await expect(page.getByRole("heading", { name: "ワークスペース設定" })).toBeVisible();
  await expect(page.getByLabel("会社・ワークスペース名")).toBeVisible();

  await page.getByLabel("会社・ワークスペース名").fill("テスト薬局");
  await page.getByRole("button", { name: "ワークスペースを作成" }).click();

  await expect(page.getByText("ワークスペースを作成しました")).toBeVisible();
});
