import { expect, test } from "@playwright/test";

test("shows the dashboard", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Consultant Copilot" })).toBeVisible();
  await expect(page.getByText("Discovery Feed")).toBeVisible();
  await expect(page.getByText("Observed facts")).toBeVisible();
  await expect(page.getByText("Report Copilot")).toBeVisible();
});
