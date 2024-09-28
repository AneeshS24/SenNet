// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    var socket = io();

    // Fetch initial network status
    fetch('/fetch-status')
        .then(response => response.json())
        .then(data => updateNetworkStatus(data));

    // Fetch external data
    fetch('/external-data')
        .then(response => response.json())
        .then(data => displayExternalData(data));

    socket.on('status_update', function(data) {
        updateNetworkStatus(data);
    });

    function updateNetworkStatus(data) {
        var blacklistedIPsContainer = document.getElementById('blacklisted-ips');
        var adSourcesContainer = document.getElementById('ad-sources');

        blacklistedIPsContainer.innerHTML = '';
        adSourcesContainer.innerHTML = '';

        if (data.blacklisted_ips.length === 0) {
            blacklistedIPsContainer.innerHTML = '<p>No blacklisted IPs found.</p>';
        } else {
            data.blacklisted_ips.forEach(function(ip) {
                var item = document.createElement('li');
                item.textContent = ip;
                blacklistedIPsContainer.appendChild(item);
            });
        }

        if (data.ad_sources.length === 0) {
            adSourcesContainer.innerHTML = '<p>No ad sources found.</p>';
        } else {
            data.ad_sources.forEach(function(source) {
                var item = document.createElement('li');
                item.textContent = source;
                adSourcesContainer.appendChild(item);
            });
        }
    }

    function displayExternalData(data) {
        var externalDataContainer = document.getElementById('external-data');

        if (data.error) {
            externalDataContainer.innerHTML = `<p>${data.error}</p>`;
        } else {
            // Assuming data is an array of items
            externalDataContainer.innerHTML = '';
            data.forEach(function(item) {
                var itemElement = document.createElement('div');
                itemElement.textContent = JSON.stringify(item); // Customize as needed
                externalDataContainer.appendChild(itemElement);
            });
        }
    }

    // Function to handle the IP check
    document.getElementById('ip-check-form').addEventListener('submit', function(event) {
        event.preventDefault();
        var ipAddress = document.getElementById('ip-address').value;
        fetch(`/check-ip?ip=${encodeURIComponent(ipAddress)}`)
            .then(response => response.json())
            .then(data => displayIPCheckResult(data))
            .catch(error => console.error("Error checking IP address:", error));
    });
    
    function displayIPCheckResult(data) {
        var resultContainer = document.getElementById('ip-check-result');
        if (data.is_blacklisted) {
            resultContainer.innerHTML = `<p>${data.ip} is blacklisted.</p>`;
        } else {
            resultContainer.innerHTML = `<p>${data.ip} is not blacklisted.</p>`;
        }
    }
    