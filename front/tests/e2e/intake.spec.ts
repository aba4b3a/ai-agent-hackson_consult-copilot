import { expect, test } from "@playwright/test";

test("business user can submit the URL report form", async ({ page }) => {
  await page.goto("/intake?form=demo");

  await expect(page.getByRole("heading", { name: "日報フォーム" })).toBeVisible();
  await expect(page.getByText("今日の質問")).toBeVisible();

  await page
    .getByLabel("気づいたこと・顧客の声")
    .fill("高齢のお客様から、駅前ドラッグのほうが待ち時間が短いと言われた。");
  await page.getByRole("button", { name: "送信" }).click();

  // Returns to the home dashboard after a successful submission.
  await expect(page.getByRole("heading", { name: "Consultant Copilot" })).toBeVisible();
});

test("business user can complete the conversational intake", async ({ page }) => {
  await page.goto("/intake/chat?ws=ws_001");

  await expect(page.getByRole("heading", { name: "会話形式の聞き取り" })).toBeVisible();

  const input = page.getByPlaceholder("話すように入力してください");
  // Answer the opener; dynamic follow-ups are then fetched and asked.
  await input.fill("競合の話が出た");
  await page.getByRole("button", { name: "Send" }).click();

  // Skip remaining follow-ups and go to the confirmation view.
  await page.getByRole("button", { name: /質問をスキップ/ }).click();
  await expect(page.getByText("送信内容の確認")).toBeVisible();
  await page.getByRole("button", { name: "この内容で送信" }).click();

  // Returns to the home dashboard after a successful submission.
  await expect(page.getByRole("heading", { name: "Consultant Copilot" })).toBeVisible();
});
