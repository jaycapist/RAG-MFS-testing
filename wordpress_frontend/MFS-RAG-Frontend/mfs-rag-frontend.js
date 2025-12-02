/*
Plugin Name: Minimal API
Description: Minimal plugin with persistent input via REST API.
Version: 1.01
Author: Kyle Bueche

Shortcode: [mfs_rag_frontend]
*/

async function queryragapi() {
    let ragOutputText = document.getElementById("rag-output-generative-text");
    ragOutputText.innerHTML = "<div class='loading-text'>🔍 Finding Documents...</div>";
    const input = document.getElementById("rag-input").value;

    console.log("starting api fetch...");
    const response = await fetch("https://rag-mfs-testing.onrender.com/query", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ query: input })
    });
    console.log("getting json...");
    const data = await response.json();
    console.log(data);
    ragOutputText.innerHTML = data.answer;
    
    ragOutputDocuments = document.getElementById("rag-output-documents");

    for (let i = 0; i < data.sources.length; i++) {
        const sourceName = data.sources[i].source;
        const sourceLink = data.sources[i].link;
        const documentEntry = `
        <div class="document-entry">
            <h4><a target="_blank" href="${sourceLink}" class="document-link">${sourceName}</a></h4>
            <div class="document-meta">Click to view document</div>
        </div>
        `
        const wrapper = document.createElement('div');
        wrapper.innerHTML = documentEntry;
        ragOutputDocuments.appendChild(wrapper);
    }
}

window.onload = function() {
    document.getElementById("myButton").onclick = function () {
        queryragapi();
    };
}
