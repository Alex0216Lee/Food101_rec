// 搜尋功能
const searchInput = document.getElementById("search-input");
const searchButton = document.getElementById("search-button");
const searchResults = document.getElementById("search-results");

// 搜尋功能
searchButton.addEventListener("click", () => {
    const query = searchInput.value.trim();

    if (!query) {
        searchResults.innerHTML = "<p>請輸入搜尋關鍵字。</p>";
        return;
    }

    // 呼叫 Flask /search API
    fetch(`/search?query=${query}`)
        .then(response => response.json())
        .then(data => {
            searchResults.innerHTML = ""; // 清空舊結果
            if (data.length === 0) {
                searchResults.innerHTML = "<p>找不到符合的食譜。</p>";
                return;
            }

            // 顯示搜尋結果
            data.forEach(item => {
                const resultItem = document.createElement("p");
                resultItem.textContent = item.title;
                resultItem.style.cursor = "pointer";
                resultItem.style.color = "blue";

                // 點擊搜尋結果時，顯示詳細資訊
                resultItem.addEventListener("click", () => showRecipeDetails(item.title));
                searchResults.appendChild(resultItem);
            });
        })
        .catch(error => {
            console.error("Error:", error);
            searchResults.innerHTML = "<p>發生錯誤，請稍後再試。</p>";
        });
});

function showRecipeDetails(title) {
    // 跳轉到新的頁面
    window.location.href = `/recipe_detail?title=${title}`;
}




// 取得 DOM 元素
const uploadInput = document.getElementById('upload-input');
const previewContainer = document.getElementById('image-preview');
const imageButtons = document.getElementById('image-buttons');
const confirmButton = document.getElementById('confirm-upload');
const cancelButton = document.getElementById('cancel-upload');
const resultsContainer = document.getElementById('transformer-results');

let uploadedFile = null;

// 當選擇圖片時
uploadInput.addEventListener('change', function (event) {
    uploadedFile = event.target.files[0];
    if (uploadedFile) {
        const reader = new FileReader();
        reader.onload = function (e) {
            previewContainer.innerHTML = `<p>圖片預覽：</p><img src="${e.target.result}" alt="預覽圖片" style="max-width: 100%;">`;
            imageButtons.style.display = "block";
        };
        reader.readAsDataURL(uploadedFile);
    } else {
        resetUpload();
    }
});

confirmButton.addEventListener('click', async function () {
    if (uploadedFile) {
        // 顯示辨識中訊息
        resultsContainer.innerHTML = "<p>圖片正在辨識中，請稍候...</p>";

        const formData = new FormData();
        formData.append("file", uploadedFile);

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData
            });
        
            if (!response.ok) throw new Error("辨識失敗");
        
            const result = await response.json();
        
            // 顯示結果
            resultsContainer.innerHTML = `
    <h3>辨識結果</h3>
    <p><a href="/recipe_detail?title=${encodeURIComponent(result.swin_prediction)}" target="_blank">${result.swin_prediction}</a></p>
`;

        } catch (error) {
            console.error("錯誤:", error); // 打印整個錯誤對象以獲取更多信息
            resultsContainer.innerHTML = `<p>辨識過程出現錯誤: ${error.message}</p>`;
        }
        
        
    }
});



// 點擊「取消重新上傳」按鈕
cancelButton.addEventListener('click', function () {
    resetUpload();
});

// 重置上傳功能
function resetUpload() {
    uploadInput.value = "";
    previewContainer.innerHTML = "";
    imageButtons.style.display = "none";
    uploadedFile = null;
}

