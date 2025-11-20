/**
 * Results Skeleton Component Tests
 *
 * Test suite for the ResultsSkeleton component covering:
 * - Rendering skeleton cards
 * - Correct count of skeletons
 * - Accessibility (aria-busy)
 * - Responsive grid layout
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { ResultsSkeleton } from "./ResultsSkeleton";

describe("ResultsSkeleton Component", () => {
  describe("Rendering", () => {
    it("renders with default count (9)", () => {
      const { container } = render(<ResultsSkeleton />);

      // Should have 9 skeleton cards
      const cards = container.querySelectorAll("[role='status']");
      expect(cards).toHaveLength(1); // The container itself has role="status"

      // Check for skeleton elements (multiple per card)
      const skeletons = container.querySelectorAll("[data-slot='skeleton']");
      expect(skeletons.length).toBeGreaterThan(9); // Each card has multiple skeletons
    });

    it("renders with custom count", () => {
      const { container } = render(<ResultsSkeleton count={5} />);

      // Check for skeleton grid items
      const gridChildren = container.querySelector(
        "[role='status']"
      )?.children;
      expect(gridChildren?.length).toBe(5);
    });

    it("renders with count of 0", () => {
      const { container } = render(<ResultsSkeleton count={0} />);

      const gridChildren = container.querySelector(
        "[role='status']"
      )?.children;
      expect(gridChildren?.length).toBe(0);
    });

    it("renders with large count", () => {
      const { container } = render(<ResultsSkeleton count={20} />);

      const gridChildren = container.querySelector(
        "[role='status']"
      )?.children;
      expect(gridChildren?.length).toBe(20);
    });
  });

  describe("Accessibility", () => {
    it("has aria-busy attribute", () => {
      const { container } = render(<ResultsSkeleton />);

      const status = screen.getByRole("status");
      expect(status).toHaveAttribute("aria-busy", "true");
    });

    it("has accessible label", () => {
      const { container } = render(<ResultsSkeleton />);

      const status = screen.getByRole("status");
      expect(status).toHaveAttribute("aria-label", "Loading results");
    });

    it("has role='status' for announcements", () => {
      render(<ResultsSkeleton />);

      expect(screen.getByRole("status")).toBeInTheDocument();
    });
  });

  describe("Styling", () => {
    it("applies grid layout classes", () => {
      const { container } = render(<ResultsSkeleton />);

      const grid = screen.getByRole("status");
      expect(grid).toHaveClass("grid");
      expect(grid).toHaveClass("grid-cols-1");
      expect(grid).toHaveClass("md:grid-cols-2");
      expect(grid).toHaveClass("lg:grid-cols-3");
    });

    it("applies custom className", () => {
      const { container } = render(
        <ResultsSkeleton className="custom-class" />
      );

      const grid = screen.getByRole("status");
      expect(grid).toHaveClass("custom-class");
    });
  });

  describe("Skeleton Card Structure", () => {
    it("renders card with proper structure", () => {
      const { container } = render(<ResultsSkeleton count={1} />);

      // Check for card container
      const card = container.querySelector(
        ".rounded-lg.border.border-input.bg-card"
      );
      expect(card).toBeInTheDocument();

      // Check for thumbnail skeleton
      const thumbnail = card?.querySelector(".aspect-video");
      expect(thumbnail).toBeInTheDocument();

      // Check for content section
      const content = card?.querySelector(".p-4");
      expect(content).toBeInTheDocument();
    });

    it("includes placeholder for video badge", () => {
      const { container } = render(<ResultsSkeleton count={1} />);

      const card = container.querySelector(
        ".rounded-lg.border.border-input.bg-card"
      );
      const badges = card?.querySelectorAll("[data-slot='skeleton']");

      // Should have multiple skeletons for badges
      expect(badges && badges.length > 0).toBe(true);
    });

    it("includes placeholder tags section", () => {
      const { container } = render(<ResultsSkeleton count={1} />);

      const card = container.querySelector(
        ".rounded-lg.border.border-input.bg-card"
      );
      const tagSkeletons = card?.querySelectorAll(
        "[data-slot='skeleton'].rounded-full"
      );

      // Should have multiple tag skeletons
      expect(tagSkeletons && tagSkeletons.length > 0).toBe(true);
    });

    it("includes metadata placeholders", () => {
      const { container } = render(<ResultsSkeleton count={1} />);

      const card = container.querySelector(
        ".rounded-lg.border.border-input.bg-card"
      );
      const skeletons = card?.querySelectorAll("[data-slot='skeleton']");

      // Should have many skeletons (thumbnail + badges + metadata + tags)
      expect(skeletons && skeletons.length > 5).toBe(true);
    });
  });

  describe("Animation", () => {
    it("applies pulse animation", () => {
      const { container } = render(<ResultsSkeleton count={1} />);

      const card = container.querySelector(
        ".rounded-lg.border.border-input.bg-card"
      );
      expect(card).toHaveClass("animate-pulse");
    });

    it("skeletons have animate-pulse class", () => {
      const { container } = render(<ResultsSkeleton count={1} />);

      const skeletons = container.querySelectorAll(
        "[data-slot='skeleton']"
      );
      skeletons.forEach((skeleton) => {
        expect(skeleton).toHaveClass("animate-pulse");
      });
    });
  });

  describe("Grid Responsiveness", () => {
    it("renders responsive grid classes", () => {
      const { container } = render(<ResultsSkeleton />);

      const grid = screen.getByRole("status");

      // Mobile: 1 column
      expect(grid).toHaveClass("grid-cols-1");

      // Tablet: 2 columns
      expect(grid).toHaveClass("md:grid-cols-2");

      // Desktop: 3 columns
      expect(grid).toHaveClass("lg:grid-cols-3");
      expect(grid).toHaveClass("xl:grid-cols-3");
    });

    it("maintains gap between cards", () => {
      const { container } = render(<ResultsSkeleton />);

      const grid = screen.getByRole("status");
      expect(grid).toHaveClass("gap-4");
    });
  });

  describe("Edge Cases", () => {
    it("handles rendering many skeletons efficiently", () => {
      const { container } = render(<ResultsSkeleton count={100} />);

      const gridChildren = container.querySelector(
        "[role='status']"
      )?.children;
      expect(gridChildren?.length).toBe(100);
    });

    it("renders without errors with count=1", () => {
      expect(() => render(<ResultsSkeleton count={1} />)).not.toThrow();
    });

    it("renders without errors with very large count", () => {
      expect(() => render(<ResultsSkeleton count={1000} />)).not.toThrow();
    });
  });
});
