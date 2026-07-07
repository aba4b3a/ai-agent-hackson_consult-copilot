import { expect, test } from "@playwright/test";

test("shows the dashboard with sidebar navigation", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Consultant Copilot" })).toBeVisible();
  await expect(page.getByText("Discovery Feed").first()).toBeVisible();
  await expect(page.getByText("Observed facts")).toBeVisible();
  await expect(page.getByText("Relationships created")).toBeVisible();
  await expect(page.getByText("Recent knowledge additions")).toBeVisible();
  await expect(page.getByText("Knowledge gaps")).toBeVisible();
  await expect(page.getByText("Recommended observations")).toBeVisible();

  // Desktop-width sidebar with section jump links.
  await expect(page.getByRole("link", { name: "Graph Viewer" })).toBeVisible();
  await expect(page.getByRole("link", { name: "ワークスペース設定" })).toBeVisible();
});

test("report copilot opens from the floating button", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Open Report Copilot" }).click();
  await expect(page.getByRole("heading", { name: "Report Copilot" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Ask copilot" })).toBeVisible();

  await page.getByRole("button", { name: "Close Report Copilot" }).click();
  await expect(page.getByRole("button", { name: "Open Report Copilot" })).toBeVisible();
});

test("hamburger opens the drawer on narrow screens", async ({ page }) => {
  await page.setViewportSize({ width: 480, height: 800 });
  await page.goto("/");

  await expect(page.getByRole("button", { name: "Open navigation" })).toBeVisible();
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.getByText("メニュー")).toBeVisible();

  await page.getByRole("button", { name: "Close", exact: true }).click();
  await expect(page.getByText("メニュー")).toBeHidden();
});
