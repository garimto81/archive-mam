/**
 * Pagination Component Tests
 *
 * Test suite for the Pagination component covering:
 * - Page navigation (next, previous, direct page selection)
 * - Disabled states
 * - Results count display
 * - Keyboard accessibility
 * - Page number calculation logic
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Pagination } from "./Pagination";
import type { PaginationMeta } from "@/types/search";

describe("Pagination Component", () => {
  // Mock pagination metadata
  const createMeta = (overrides?: Partial<PaginationMeta>): PaginationMeta => ({
    currentPage: 1,
    totalPages: 5,
    pageSize: 20,
    totalResults: 100,
    hasNext: true,
    hasPrev: false,
    ...overrides
  });

  describe("Rendering", () => {
    it("renders pagination controls", () => {
      const meta = createMeta();
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      expect(screen.getByRole("navigation", { name: /pagination/i })).toBeInTheDocument();
    });

    it("displays results count correctly", () => {
      const meta = createMeta({ currentPage: 2, totalResults: 150 });
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      expect(screen.getByText(/showing 21 to 40 of 150 results/i)).toBeInTheDocument();
    });

    it("displays page numbers within range", () => {
      const meta = createMeta({ currentPage: 1, totalPages: 5 });
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      expect(screen.getByRole("button", { name: /go to page 1/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /go to page 5/i })).toBeInTheDocument();
    });
  });

  describe("Navigation", () => {
    it("calls onNextPage when next button is clicked", async () => {
      const user = userEvent.setup();
      const meta = createMeta();
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      const nextButton = screen.getByRole("button", { name: /next page/i });
      await user.click(nextButton);

      expect(handleNext).toHaveBeenCalledTimes(1);
    });

    it("calls onPrevPage when previous button is clicked", async () => {
      const user = userEvent.setup();
      const meta = createMeta({ currentPage: 2, hasPrev: true });
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      const prevButton = screen.getByRole("button", { name: /previous page/i });
      await user.click(prevButton);

      expect(handlePrev).toHaveBeenCalledTimes(1);
    });

    it("calls onPageChange with correct page number", async () => {
      const user = userEvent.setup();
      const meta = createMeta();
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      const pageButton = screen.getByRole("button", { name: /go to page 3/i });
      await user.click(pageButton);

      expect(handlePageChange).toHaveBeenCalledWith(3);
    });
  });

  describe("Disabled States", () => {
    it("disables next button when no next page", () => {
      const meta = createMeta({ totalPages: 5, currentPage: 5, hasNext: false });
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      const nextButton = screen.getByRole("button", { name: /next page/i });
      expect(nextButton).toBeDisabled();
    });

    it("disables previous button when no previous page", () => {
      const meta = createMeta({ currentPage: 1, hasPrev: false });
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      const prevButton = screen.getByRole("button", { name: /previous page/i });
      expect(prevButton).toBeDisabled();
    });

    it("disables all controls when disabled prop is true", () => {
      const meta = createMeta();
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
          disabled={true}
        />
      );

      const buttons = screen.getAllByRole("button");
      buttons.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });
  });

  describe("Page Number Calculation", () => {
    it("shows all pages if less than max display", () => {
      const meta = createMeta({ totalPages: 3 });
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      expect(screen.getByRole("button", { name: /go to page 1/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /go to page 2/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /go to page 3/i })).toBeInTheDocument();
    });

    it("shows ellipsis for large page counts", () => {
      const meta = createMeta({ totalPages: 20, currentPage: 10 });
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      // Should show: 1, ..., current-1, current, current+1, ..., last
      expect(screen.getByRole("button", { name: /go to page 1/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /go to page 20/i })).toBeInTheDocument();
      // Ellipsis are aria-hidden
      const ellipsis = screen.getAllByText("...");
      expect(ellipsis.length).toBeGreaterThan(0);
    });
  });

  describe("Accessibility", () => {
    it("has proper ARIA labels", () => {
      const meta = createMeta();
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      expect(screen.getByRole("navigation", { name: /pagination/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /previous page/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /next page/i })).toBeInTheDocument();
    });

    it("marks current page with aria-current", () => {
      const meta = createMeta({ currentPage: 2 });
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      const currentPageButton = screen.getByRole("button", { name: /go to page 2/i });
      expect(currentPageButton).toHaveAttribute("aria-current", "page");
    });

    it("is keyboard navigable", async () => {
      const user = userEvent.setup();
      const meta = createMeta();
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      const nextButton = screen.getByRole("button", { name: /next page/i });
      nextButton.focus();
      expect(nextButton).toHaveFocus();

      await user.keyboard("{Enter}");
      expect(handleNext).toHaveBeenCalled();
    });
  });

  describe("Responsive Design", () => {
    it("renders with responsive class names", () => {
      const meta = createMeta();
      const handlePageChange = jest.fn();
      const handleNext = jest.fn();
      const handlePrev = jest.fn();

      const { container } = render(
        <Pagination
          meta={meta}
          onPageChange={handlePageChange}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
        />
      );

      const nav = screen.getByRole("navigation");
      expect(nav).toHaveClass("flex", "flex-col", "sm:flex-row");
    });
  });
});
