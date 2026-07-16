import { expect, test } from "@playwright/test";
import { mockApi } from "./mock-api";

test("shows the dashboard", async ({ page }) => {
  await mockApi(page);
  await page.goto("/");

  await expect(page.getByText("Discovery Feed")).toBeVisible();
  await expect(page.getByText("Observed facts")).toBeVisible();
  await expect(page.getByRole("button", { name: /Report Copilot/ })).toBeVisible();
});
