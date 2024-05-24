document.getElementById('stockForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const url =  'https://7000-01hygkvng4h65en1z1b7mtfd9p.cloudspaces.litng.ai/predict';
    const ticker = document.getElementById('ticker').value;
    const purchaseDate = document.getElementById('purchaseDate').value;
    const shares = document.getElementById('shares').value;
    const responseContainer = document.getElementById('response');
    responseContainer.textContent = '';

    if (!ticker || !purchaseDate || !shares) {
        alert('All fields are required.');
        return;
    }

    const requestBody = {
        ticker: ticker,
        purchase_date: purchaseDate,
        shares: parseInt(shares)
    };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Accept': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (response.ok) {
            const data = await response.json(); 
            const text = data.response; 
            console.log('Data'+ data);      
            console.log('Text'+ text);
            typeText(responseContainer, text);
        } else {
            const errorText = await response.text();
            responseContainer.textContent = `Failed to fetch data: ${errorText}`;
        }
    } catch (error) {
        responseContainer.textContent = `Error: ${error.message}`;
    }
});

function typeText(element, text) {
    let i = 0;
    element.textContent = ''; // Clear the text content first
    element.style.height = 'auto'; // Reset height before calculating new height

    function updateHeight() {
        element.style.height = 'auto';
        element.style.height = `${element.scrollHeight}px`; // Adjust height based on scroll height
    }

    const interval = setInterval(() => {
        element.textContent += text.charAt(i);
        i++;
        updateHeight();
        if (i === text.length) {
            clearInterval(interval);
        }
    }, 50);
}
