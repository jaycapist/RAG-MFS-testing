/*
Plugin Name: Minimal API
Description: Minimal plugin with persistent input via REST API.
Version: 1.0
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
}
function outputDocuments() {
    ragOutputDocuments = document.getElementById("rag-output-documents");
    documents = [];
    documents.push({
        docUrl: "https://drive.google.com/file/d/1outes8jvthnMdauDKI8c7f2zejPqkHwh/preview",
        docTitle: "Senate_Aloha_Resolution"
    });
    documents.push({
        docUrl: "https://drive.google.com/file/d/1outes8jvthnMdauDKI8c7f2zejPqkHwh/preview",
        docTitle: "Another_Resolution"
    });
    documents.push({
        docUrl: "https://drive.google.com/file/d/1outes8jvthnMdauDKI8c7f2zejPqkHwh/preview",
        docTitle: "Senate_Document"
    });
    documents.push({
        docUrl: "https://drive.google.com/file/d/1outes8jvthnMdauDKI8c7f2zejPqkHwh/preview",
        docTitle: "Senate_Example_Resolution"
    });
    documents.push({
        docUrl: "https://drive.google.com/file/d/1outes8jvthnMdauDKI8c7f2zejPqkHwh/preview",
        docTitle: "Senate_Example_Resolution_2"
    });

    for (let i = 0; i < documents.length; i++) {
        const documentEntry = `
        <div class="document-entry">
            <h4><a target="_blank" href="${documents[i].docUrl}" class="document-link">${documents[i].docTitle}</a></h4>
            <div class="document-meta">Click to view document</div>
        </div>
        `
        const wrapper = document.createElement('div');
        wrapper.innerHTML = documentEntry;
        ragOutputDocuments.appendChild(wrapper);
    }
};

window.onload = function() {
    document.getElementById("myButton").onclick = function () {
        outputDocuments();
    };
}