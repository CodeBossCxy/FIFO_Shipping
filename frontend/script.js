async function load_shipper(){
    console.log("Successfully loaded");
    const response = await fetch('/api/get_valid_shippers',
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }
    );
    const shippers = await response.json();
    console.log("Shipper =", shippers);

    if (shippers.length == 0){
        return;
    }

    let html = '<ul>';
    shippers.forEach(shipper => {
        html += `<li>${shipper}</li>`;
    });
    html += '</ul>';
    console.log("HTML =", html);
    document.getElementById('shipper_list').innerHTML = html;
}

load_shipper();