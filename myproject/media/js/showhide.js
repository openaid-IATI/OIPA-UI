function showSlidingDiv(){
		var min = document.getElementById("s1min");
		var plus = document.getElementById("s1plus");
		if(min.style.display == "block") {
			min.style.display = "none";
			plus.style.display = "block";
		}
		else {
			document.getElementById("s1plus").style.display = "none";
			document.getElementById("s2plus").style.display = "block";
			document.getElementById("s3plus").style.display = "block";
			document.getElementById("s4plus").style.display = "block";
			document.getElementById("s5plus").style.display = "block";
			document.getElementById("s6plus").style.display = "block";
			document.getElementById("s7plus").style.display = "block";
			document.getElementById("s8plus").style.display = "block";
			document.getElementById("s9plus").style.display = "block";
			document.getElementById("s1min").style.display = "block";
			document.getElementById("s2min").style.display = "none";
			document.getElementById("s3min").style.display = "none";
			document.getElementById("s4min").style.display = "none";
			document.getElementById("s5min").style.display = "none";
			document.getElementById("s6min").style.display = "none";
			document.getElementById("s7min").style.display = "none";
			document.getElementById("s8min").style.display = "none";
			document.getElementById("s9min").style.display = "none";
		}
        $("#slidingDiv").animate({"height": "toggle"}, { duration: 1000 });
        $("#slidingDiv2").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv3").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv4").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv5").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv6").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv7").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv8").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv9").animate({"height": "hide"}, { duration: 700 });				
}

function showSlidingDiv2(){
		var min = document.getElementById("s2min");
		var plus = document.getElementById("s2plus");
		if(min.style.display == "block") {
			min.style.display = "none";
			plus.style.display = "block";
		}
		else {
			document.getElementById("s1plus").style.display = "block";
			document.getElementById("s2plus").style.display = "none";
			document.getElementById("s3plus").style.display = "block";
			document.getElementById("s4plus").style.display = "block";
			document.getElementById("s5plus").style.display = "block";
			document.getElementById("s6plus").style.display = "block";
			document.getElementById("s7plus").style.display = "block";
			document.getElementById("s8plus").style.display = "block";
			document.getElementById("s9plus").style.display = "block";
			document.getElementById("s1min").style.display = "none";
			document.getElementById("s2min").style.display = "block";
			document.getElementById("s3min").style.display = "none";
			document.getElementById("s4min").style.display = "none";
			document.getElementById("s5min").style.display = "none";
			document.getElementById("s6min").style.display = "none";
			document.getElementById("s7min").style.display = "none";
			document.getElementById("s8min").style.display = "none";
			document.getElementById("s9min").style.display = "none";
		}
        $("#slidingDiv").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv2").animate({"height": "toggle"}, { duration: 1000 });
        $("#slidingDiv3").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv4").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv5").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv6").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv7").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv8").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv9").animate({"height": "hide"}, { duration: 700 });			
}

function showSlidingDiv3(){
		var min = document.getElementById("s3min");
		var plus = document.getElementById("s3plus");
		if(min.style.display == "block") {
			min.style.display = "none";
			plus.style.display = "block";
		}
		else {
			document.getElementById("s1plus").style.display = "block";
			document.getElementById("s2plus").style.display = "block";
			document.getElementById("s3plus").style.display = "none";
			document.getElementById("s4plus").style.display = "block";
			document.getElementById("s5plus").style.display = "block";
			document.getElementById("s6plus").style.display = "block";
			document.getElementById("s7plus").style.display = "block";
			document.getElementById("s8plus").style.display = "block";
			document.getElementById("s9plus").style.display = "block";
			document.getElementById("s1min").style.display = "none";
			document.getElementById("s2min").style.display = "none";
			document.getElementById("s3min").style.display = "block";
			document.getElementById("s4min").style.display = "none";
			document.getElementById("s5min").style.display = "none";
			document.getElementById("s6min").style.display = "none";
			document.getElementById("s7min").style.display = "none";
			document.getElementById("s8min").style.display = "none";
			document.getElementById("s9min").style.display = "none";
		}
        $("#slidingDiv").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv2").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv3").animate({"height": "toggle"}, { duration: 1000 });		
        $("#slidingDiv4").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv5").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv6").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv7").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv8").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv9").animate({"height": "hide"}, { duration: 700 });	
}		

function showSlidingDiv4(){
		var min = document.getElementById("s4min");
		var plus = document.getElementById("s4plus");
		if(min.style.display == "block") {
			min.style.display = "none";
			plus.style.display = "block";
		}
		else {
			document.getElementById("s1plus").style.display = "block";
			document.getElementById("s2plus").style.display = "block";
			document.getElementById("s3plus").style.display = "block";
			document.getElementById("s4plus").style.display = "none";
			document.getElementById("s5plus").style.display = "block";
			document.getElementById("s6plus").style.display = "block";
			document.getElementById("s7plus").style.display = "block";
			document.getElementById("s8plus").style.display = "block";
			document.getElementById("s9plus").style.display = "block";
			document.getElementById("s1min").style.display = "none";
			document.getElementById("s2min").style.display = "none";
			document.getElementById("s3min").style.display = "none";
			document.getElementById("s4min").style.display = "block";
			document.getElementById("s5min").style.display = "none";
			document.getElementById("s6min").style.display = "none";
			document.getElementById("s7min").style.display = "none";
			document.getElementById("s8min").style.display = "none";
			document.getElementById("s9min").style.display = "none";
		}
        $("#slidingDiv").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv2").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv3").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv4").animate({"height": "toggle"}, { duration: 1000 });	
        $("#slidingDiv5").animate({"height": "hide"}, { duration: 700 });			
        $("#slidingDiv6").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv7").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv8").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv9").animate({"height": "hide"}, { duration: 700 });			
}

function showSlidingDiv5(){
		var min = document.getElementById("s5min");
		var plus = document.getElementById("s5plus");
		if(min.style.display == "block") {
			min.style.display = "none";
			plus.style.display = "block";
		}
		else {
			document.getElementById("s1plus").style.display = "block";
			document.getElementById("s2plus").style.display = "block";
			document.getElementById("s3plus").style.display = "block";
			document.getElementById("s4plus").style.display = "block";
			document.getElementById("s5plus").style.display = "none";
			document.getElementById("s6plus").style.display = "block";
			document.getElementById("s7plus").style.display = "block";
			document.getElementById("s8plus").style.display = "block";
			document.getElementById("s9plus").style.display = "block";
			document.getElementById("s1min").style.display = "none";
			document.getElementById("s2min").style.display = "none";
			document.getElementById("s3min").style.display = "none";
			document.getElementById("s4min").style.display = "none";
			document.getElementById("s5min").style.display = "block";
			document.getElementById("s6min").style.display = "none";
			document.getElementById("s7min").style.display = "none";
			document.getElementById("s8min").style.display = "none";
			document.getElementById("s9min").style.display = "none";
		}
        $("#slidingDiv").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv2").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv3").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv4").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv5").animate({"height": "toggle"}, { duration: 1000 });	
        $("#slidingDiv6").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv7").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv8").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv9").animate({"height": "hide"}, { duration: 700 });			
}


function showSlidingDiv6(){
		var min = document.getElementById("s6min");
		var plus = document.getElementById("s6plus");
		if(min.style.display == "block") {
			min.style.display = "none";
			plus.style.display = "block";
		}
		else {
			document.getElementById("s1plus").style.display = "block";
			document.getElementById("s2plus").style.display = "block";
			document.getElementById("s3plus").style.display = "block";
			document.getElementById("s4plus").style.display = "block";
			document.getElementById("s5plus").style.display = "block";
			document.getElementById("s6plus").style.display = "none";
			document.getElementById("s7plus").style.display = "block";
			document.getElementById("s8plus").style.display = "block";
			document.getElementById("s9plus").style.display = "block";
			document.getElementById("s1min").style.display = "none";
			document.getElementById("s2min").style.display = "none";
			document.getElementById("s3min").style.display = "none";
			document.getElementById("s4min").style.display = "none";
			document.getElementById("s5min").style.display = "none";
			document.getElementById("s6min").style.display = "block";
			document.getElementById("s7min").style.display = "none";
			document.getElementById("s8min").style.display = "none";
			document.getElementById("s9min").style.display = "none";
		}
        $("#slidingDiv").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv2").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv3").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv4").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv5").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv6").animate({"height": "toggle"}, { duration: 1000 });		
        $("#slidingDiv7").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv8").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv9").animate({"height": "hide"}, { duration: 700 });			
}


function showSlidingDiv7(){
		if(document.getElementById("s7min").style.display == "block") {
			document.getElementById("s7plus").style.display = "block";
		}
		else {
			document.getElementById("s1plus").style.display = "block";
			document.getElementById("s2plus").style.display = "block";
			document.getElementById("s3plus").style.display = "block";
			document.getElementById("s4plus").style.display = "block";
			document.getElementById("s5plus").style.display = "block";
			document.getElementById("s6plus").style.display = "block";
			document.getElementById("s7plus").style.display = "none";
			document.getElementById("s8plus").style.display = "block";
			document.getElementById("s9plus").style.display = "block";
			document.getElementById("s1min").style.display = "none";
			document.getElementById("s2min").style.display = "none";
			document.getElementById("s3min").style.display = "none";
			document.getElementById("s4min").style.display = "none";
			document.getElementById("s5min").style.display = "none";
			document.getElementById("s6min").style.display = "none";
			document.getElementById("s7min").style.display = "block";
			document.getElementById("s8min").style.display = "none";
			document.getElementById("s9min").style.display = "none";
		}
        $("#slidingDiv").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv2").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv3").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv4").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv5").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv6").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv7").animate({"height": "toggle"}, { duration: 1000 });
        $("#slidingDiv8").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv9").animate({"height": "hide"}, { duration: 700 });			
}

function showSlidingDiv8(){
		var min = document.getElementById("s8min");
		var plus = document.getElementById("s8plus");
		if(min.style.display == "block") {
			min.style.display = "none";
			plus.style.display = "block";
		}
		else {
			document.getElementById("s1plus").style.display = "block";
			document.getElementById("s2plus").style.display = "block";
			document.getElementById("s3plus").style.display = "block";
			document.getElementById("s4plus").style.display = "block";
			document.getElementById("s5plus").style.display = "block";
			document.getElementById("s6plus").style.display = "block";
			document.getElementById("s7plus").style.display = "block";
			document.getElementById("s8plus").style.display = "none";
			document.getElementById("s9plus").style.display = "block";
			document.getElementById("s1min").style.display = "none";
			document.getElementById("s2min").style.display = "none";
			document.getElementById("s3min").style.display = "none";
			document.getElementById("s4min").style.display = "none";
			document.getElementById("s5min").style.display = "none";
			document.getElementById("s6min").style.display = "none";
			document.getElementById("s7min").style.display = "none";
			document.getElementById("s8min").style.display = "block";
			document.getElementById("s9min").style.display = "none";
		}
        $("#slidingDiv").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv2").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv3").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv4").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv5").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv6").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv7").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv8").animate({"height": "toggle"}, { duration: 1000 });	
        $("#slidingDiv9").animate({"height": "hide"}, { duration: 700 });			
}

function showSlidingDiv9(){
		var min = document.getElementById("s9min");
		var plus = document.getElementById("s9plus");
		if(min.style.display == "block") {
			min.style.display = "none";
			plus.style.display = "block";
		}
		else {
			document.getElementById("s1plus").style.display = "block";
			document.getElementById("s2plus").style.display = "block";
			document.getElementById("s3plus").style.display = "block";
			document.getElementById("s4plus").style.display = "block";
			document.getElementById("s5plus").style.display = "block";
			document.getElementById("s6plus").style.display = "block";
			document.getElementById("s7plus").style.display = "block";
			document.getElementById("s8plus").style.display = "block";
			document.getElementById("s9plus").style.display = "none";
			document.getElementById("s1min").style.display = "none";
			document.getElementById("s2min").style.display = "none";
			document.getElementById("s3min").style.display = "none";
			document.getElementById("s4min").style.display = "none";
			document.getElementById("s5min").style.display = "none";
			document.getElementById("s6min").style.display = "none";
			document.getElementById("s7min").style.display = "none";
			document.getElementById("s8min").style.display = "none";
			document.getElementById("s9min").style.display = "block";
		}
        $("#slidingDiv").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv2").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv3").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv4").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv5").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv6").animate({"height": "hide"}, { duration: 700 });		
        $("#slidingDiv7").animate({"height": "hide"}, { duration: 700 });
        $("#slidingDiv8").animate({"height": "hide"}, { duration: 700 });	
        $("#slidingDiv9").animate({"height": "toggle"}, { duration: 1000 });			
}

function showMap(){
		if(document.getElementById("showm").style.display == "block") {
			document.getElementById("showm").style.display = "none";
			document.getElementById("hidem").style.display = "block";
		}
		else {
			document.getElementById("showm").style.display = "block";
			document.getElementById("hidem").style.display = "none";
		}	
        $("#showMap").animate({"height": "toggle"}, { duration: 1000 });			
}