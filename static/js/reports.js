document.addEventListener("DOMContentLoaded", () => {

    // ========================================================
    // DATE FILTER
    // ========================================================

    const periodSelect = document.getElementById("report-period");
    const singleDate = document.getElementById("report-single-date");
    const dateRange = document.getElementById("report-date-range");

    function updateDateFields() {
        if (!periodSelect) return;

        const period = periodSelect.value;

        if (singleDate) {
            singleDate.classList.toggle(
                "hidden",
                period !== "date"
            );
        }

        if (dateRange) {
            dateRange.classList.toggle(
                "hidden",
                period !== "range"
            );
        }
    }

    if (periodSelect) {
        periodSelect.addEventListener(
            "change",
            updateDateFields
        );

        updateDateFields();
    }


    // ========================================================
    // OVERVIEW SVG CHART
    // ========================================================

    const chartContainer = document.getElementById(
        "reports-weekly-chart"
    );

    const chartDataElement = document.getElementById(
        "reports-chart-data"
    );

    if (!chartContainer || !chartDataElement) {
        return;
    }

    let chartData = [];

    try {
        chartData = JSON.parse(chartDataElement.textContent);
    } catch (error) {
        chartContainer.textContent = "Unable to load chart.";
        return;
    }

    if (!Array.isArray(chartData) || !chartData.length) {
        chartContainer.textContent = "No chart data available.";
        return;
    }

    const NS = "http://www.w3.org/2000/svg";

    function svgElement(tag, attributes = {}, text = null) {
        const element = document.createElementNS(NS, tag);

        Object.entries(attributes).forEach(([key, value]) => {
            element.setAttribute(key, String(value));
        });

        if (text !== null) {
            element.textContent = String(text);
        }

        return element;
    }

    const svg = svgElement("svg", {
        viewBox: "0 0 760 270",
        width: "100%",
        height: "100%",
        role: "img",
        "aria-label": "Gross sales and refunds for the last seven days"
    });

    const width = 760;
    const height = 270;

    const left = 52;
    const right = 20;
    const top = 20;
    const bottom = 45;

    const plotWidth = width - left - right;
    const plotHeight = height - top - bottom;

    const maxValue = Math.max(
        1,
        ...chartData.flatMap((day) => [
            Number(day.gross) || 0,
            Number(day.refunds) || 0
        ])
    );

    // Grid lines and Y-axis labels
    for (let i = 0; i <= 4; i++) {
        const value = maxValue * (i / 4);

        const y = top + plotHeight - (
            value / maxValue
        ) * plotHeight;

        svg.appendChild(
            svgElement("line", {
                x1: left,
                y1: y,
                x2: width - right,
                y2: y,
                stroke: "#e5e7eb",
                "stroke-width": 1
            })
        );

        svg.appendChild(
            svgElement("text", {
                x: left - 10,
                y: y + 4,
                "text-anchor": "end",
                "font-size": 11,
                fill: "#6b7280"
            }, `£${Math.round(value)}`)
        );
    }

    const groupWidth = plotWidth / chartData.length;
    const barWidth = Math.min(24, groupWidth * 0.27);

    chartData.forEach((day, index) => {

        const gross = Math.max(0, Number(day.gross) || 0);
        const refunds = Math.max(0, Number(day.refunds) || 0);

        const center = left + groupWidth * (index + 0.5);

        const grossHeight = gross / maxValue * plotHeight;
        const refundHeight = refunds / maxValue * plotHeight;

        // Gross Sales bar
        const grossBar = svgElement("rect", {
            x: center - barWidth - 3,
            y: top + plotHeight - grossHeight,
            width: barWidth,
            height: grossHeight,
            rx: 3,
            fill: "#15803d"
        });

        grossBar.appendChild(
            svgElement(
                "title",
                {},
                `${day.date}: Gross Sales £${gross.toFixed(2)}`
            )
        );

        svg.appendChild(grossBar);

        // Refunds bar
        const refundBar = svgElement("rect", {
            x: center + 3,
            y: top + plotHeight - refundHeight,
            width: barWidth,
            height: refundHeight,
            rx: 3,
            fill: "#ef4444"
        });

        refundBar.appendChild(
            svgElement(
                "title",
                {},
                `${day.date}: Refunds £${refunds.toFixed(2)}`
            )
        );

        svg.appendChild(refundBar);

        // Day label
        svg.appendChild(
            svgElement("text", {
                x: center,
                y: height - 17,
                "text-anchor": "middle",
                "font-size": 12,
                fill: "#6b7280"
            }, day.label)
        );

    });

    chartContainer.replaceChildren(svg);

    // Chart legend
    const legend = document.createElement("div");

    legend.className =
        "mt-3 flex flex-wrap justify-center gap-5 text-xs text-text-muted";

    const entries = [
        ["#15803d", "Gross Sales"],
        ["#ef4444", "Refunds"]
    ];

    entries.forEach(([color, label]) => {
        const item = document.createElement("div");

        item.className = "flex items-center gap-2";

        const marker = document.createElement("span");

        marker.className = "h-3 w-3 rounded-sm";
        marker.style.backgroundColor = color;

        const text = document.createElement("span");
        text.textContent = label;

        item.append(marker, text);
        legend.appendChild(item);
    });

    chartContainer.insertAdjacentElement(
        "afterend",
        legend
    );

});