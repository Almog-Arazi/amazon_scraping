async function search() {
    const searchQuery = document.getElementById("search-query").value;
    const response = await fetch("/result", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `search_query=${encodeURIComponent(searchQuery)}`
    });
    const resultHTML = await response.text();
    document.open();
    document.write(resultHTML);
    document.close();
}
