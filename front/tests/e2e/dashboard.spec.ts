import { expect, test } from "@playwright/test";

test("shows the dashboard", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Quality Dashboard" })).toBeVisible();
  await expect(page.getByText("Quality Score")).toBeVisible();
  await expect(page.getByText("Human Approval Required")).toBeVisible();
});
