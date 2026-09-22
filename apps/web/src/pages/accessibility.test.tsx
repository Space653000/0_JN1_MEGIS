import axe from "axe-core";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../App";
import { initialPrototypeModel } from "../adapters/prototype-adapter";
import { DesignPage } from "./DesignPage";

afterEach(() => {
  cleanup();
  window.localStorage.clear();
  window.history.replaceState({}, "", "/progress");
});

async function expectNoWcagViolations(path: string) {
  window.history.replaceState({}, "", path);
  render(<App />);
  const result = await axe.run(document.body, {
    runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"] },
    rules: {
      // jsdom has no layout or canvas. Contrast is covered by deterministic
      // palette ratio tests and remains part of the required browser/manual audit.
      "color-contrast": { enabled: false },
    },
  });
  expect(result.violations, JSON.stringify(result.violations, null, 2)).toEqual([]);
}

describe("G6-A11Y-001 automated WCAG checks", () => {
  for (const path of ["/progress", "/design", "/review", "/results", "/roadmap"]) {
    it(`${path} has no axe WCAG 2.2 A/AA violation`, async () => {
      await expectNoWcagViolations(path);
    });
  }

  it("exposes a skip link and moves focus to main content after navigation", async () => {
    window.history.replaceState({}, "", "/progress");
    render(<App />);
    expect(screen.getByRole("link", { name: "跳至主要內容" })).toHaveAttribute("href", "#main-content");
    fireEvent.click(screen.getByRole("button", { name: /設計工作台/ }));
    await waitFor(() => expect(screen.getByRole("main")).toHaveFocus());
    expect(screen.getByRole("button", { name: /設計工作台/ })).toHaveAttribute("aria-current", "page");
  });

  it("returns mobile navigation focus to the menu button on Escape", () => {
    render(<App />);
    const open = screen.getByRole("button", { name: "開啟導覽" });
    fireEvent.click(open);
    expect(open).toHaveAttribute("aria-expanded", "true");
    const close = screen.getByRole("button", { name: "關閉導覽" });
    expect(close).toHaveFocus();
    const last = screen.getByRole("button", { name: /建設路線圖/ });
    last.focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(close).toHaveFocus();
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(last).toHaveFocus();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(open).toHaveAttribute("aria-expanded", "false");
    expect(open).toHaveFocus();
  });

  it("announces selected choice-card state with aria-pressed", () => {
    render(<DesignPage model={initialPrototypeModel} setModel={() => undefined} onNext={() => undefined} />);
    expect(screen.getByRole("button", { name: /2 片 PCB/ })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: /1 片 PCB/ })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: /USB-C/ })).toHaveAttribute("aria-pressed", "true");
  });
});

function luminance(hex: string): number {
  const channels = hex.match(/[a-f\d]{2}/gi)?.map((value) => parseInt(value, 16) / 255) ?? [];
  const linear = channels.map((value) => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}

function contrast(foreground: string, background: string): number {
  const [light, dark] = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (light + 0.05) / (dark + 0.05);
}

it("core text and status palettes meet WCAG AA normal-text contrast", () => {
  const pairs = [
    ["#eaf2f5", "#071014"],
    ["#edf6f8", "#0b171c"],
    ["#8ca2aa", "#071014"],
    ["#5de2d6", "#071014"],
    ["#ffbc5b", "#071014"],
    ["#8df1e9", "#123637"],
    ["#8ae3b5", "#123125"],
    ["#ffa490", "#3a201c"],
  ];
  for (const [foreground, background] of pairs) {
    expect(contrast(foreground, background), `${foreground} on ${background}`).toBeGreaterThanOrEqual(4.5);
  }
});
